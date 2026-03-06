# Multi-Agent Code Generation Template Handling Bugfix Design

## Overview

The multi-agent code generation system fails to properly utilize the SB Admin 2 template when generating web applications. Three interconnected bugs prevent generated applications from functioning:

1. **Missing Template Assets**: The project_builder creates empty directories but never copies template assets (vendor/, css/, js/, img/) from the template/ folder to generated projects
2. **Excessive Template Truncation**: The generator truncates template files to 6000 characters each and limits total context to 32000 characters, providing incomplete information to the LLM
3. **Missing Template Metadata**: The planner doesn't communicate which template assets should be copied versus generated, leaving the generator and builder without guidance

The fix will implement a template asset copying mechanism, improve template context delivery, and add template structure metadata to architecture plans.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bugs - when a web application is generated using the SB Admin 2 template
- **Property (P)**: The desired behavior - generated projects should include all necessary template assets and function correctly
- **Preservation**: Existing non-template file generation (backend Python files, requirements.txt) that must remain unchanged
- **Template Assets**: Static files from template/ folder (vendor libraries, CSS, JS, images) that should be copied as-is
- **Generated Files**: Code files created by the LLM (HTML, Python, custom JS/CSS) based on user requirements
- **Architecture Plan**: JSON structure produced by planner.py defining project structure and file list
- **Template Context**: Template file content provided to the LLM for reference when generating code
- **project_builder**: Module in project_builder.py that creates directory structure and writes files
- **generator**: Module in generator.py that calls LLM to generate code for each file
- **planner**: Module in planner.py that creates architecture plans

## Bug Details

### Fault Condition

The bugs manifest when the system generates a web application that uses the SB Admin 2 template. The project_builder only creates empty directories without copying template assets, the generator provides truncated template context to the LLM, and the planner doesn't specify which template files are needed.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type GenerationJob
  OUTPUT: boolean
  
  RETURN input.plan.frontend == "SB Admin 2 (Bootstrap 4)"
         AND input.plan.files contains HTML files
         AND templateAssetsExist("template/")
         AND NOT templateAssetsCopied(input.job_id)
END FUNCTION
```

### Examples

- **Bug 1 - Missing Assets**: User requests "task management dashboard". System generates index.html referencing `vendor/bootstrap/js/bootstrap.bundle.min.js`, but this file doesn't exist in generated_apps/job_abc123/, causing broken page
- **Bug 2 - Truncated Context**: Generator loads template/index.html (15KB) but truncates to 6000 chars, cutting off the footer and script sections. LLM generates incomplete HTML missing critical Bootstrap initialization
- **Bug 3 - No Metadata**: Planner generates architecture plan with `frontend/index.html` but doesn't specify that vendor/, css/, js/ folders should be copied. Builder has no guidance on what to copy
- **Edge Case - Backend Only**: User requests "REST API only, no frontend". System should NOT copy template assets (expected behavior - no bug)

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Backend Python file generation (main.py, database.py, models.py, routes/) must continue to work exactly as before
- Non-template file generation (requirements.txt, README.md, backend files) must remain unchanged
- Architecture plan validation (required fields, file list format) must remain unchanged
- Job lifecycle management (status tracking, database persistence) must remain unchanged
- Path sanitization security checks must remain unchanged
- LLM provider selection (Groq vs HuggingFace) must remain unchanged
- Markdown fence stripping from LLM output must remain unchanged

**Scope:**
All inputs that do NOT involve frontend template-based generation should be completely unaffected by this fix. This includes:
- Backend-only API projects without HTML frontend
- Projects using different frontend frameworks (if supported in future)
- Database schema generation
- Python package dependency management

## Hypothesized Root Cause

Based on the bug description and code analysis, the root causes are:

1. **Missing Copy Logic**: The project_builder.create_project_structure() function only creates empty directories using os.makedirs(). There is NO code to copy template assets from template/ to the generated project directory. The function iterates through plan["files"] to create directories but never copies static assets.

2. **Aggressive Truncation Strategy**: The generator._build_asset_context() function implements hard limits:
   - Individual files truncated to 6000 characters: `if len(content) > 6000: content = content[:6000] + "\n... (truncated)"`
   - Total context capped at 32000 characters: `MAX_TOTAL = 32000`
   - This was likely intended to stay within LLM token limits but is too aggressive, cutting off critical template structure information

3. **Planner Lacks Template Awareness**: The planner.py PLANNER_SYSTEM_PROMPT mentions the template in instructions but the generated architecture plan JSON has no field for template metadata. The plan only contains `{"project_name", "description", "backend", "frontend", "database", "files"}` without specifying which template assets to copy.

4. **No Template Asset Manifest**: There's no data structure tracking which template files should be copied for a given project type. The system doesn't distinguish between "copy as-is" (vendor libraries) and "generate from template" (HTML pages).

## Correctness Properties

Property 1: Fault Condition - Template Assets Copied to Generated Projects

_For any_ generation job where the architecture plan specifies a frontend using the SB Admin 2 template, the fixed project_builder SHALL copy all necessary template assets (vendor/, css/, js/, img/ folders) from the template/ directory to the generated project directory, ensuring all referenced files exist at the correct paths.

**Validates: Requirements 2.1, 2.4**

Property 2: Fault Condition - Complete Template Context Provided

_For any_ file generation where the file type is HTML, CSS, or JS and requires template context, the fixed generator SHALL provide sufficient template structural information to the LLM without excessive truncation, enabling the LLM to properly adapt the template structure.

**Validates: Requirements 2.2, 2.5**

Property 3: Fault Condition - Template Metadata in Architecture Plans

_For any_ architecture plan generated for a web application using the SB Admin 2 template, the fixed planner SHALL include template structure metadata specifying which template assets should be copied to the generated project.

**Validates: Requirements 2.3**

Property 4: Preservation - Non-Template File Generation Unchanged

_For any_ file generation where the file is NOT a frontend template file (backend Python files, requirements.txt, database files), the fixed system SHALL produce exactly the same generated code as the original system, preserving all existing backend generation functionality.

**Validates: Requirements 3.2, 3.6**

Property 5: Preservation - Pipeline Orchestration Unchanged

_For any_ generation job, the fixed orchestrator SHALL execute the pipeline steps (prompt → planner → generator → file builder) in the same order with the same status tracking as the original system, preserving all job lifecycle management functionality.

**Validates: Requirements 3.1, 3.4, 3.5**

Property 6: Preservation - Security Checks Unchanged

_For any_ file path operation, the fixed project_builder SHALL apply the same path sanitization and directory traversal prevention as the original system, preserving all security protections.

**Validates: Requirements 3.3**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `project_builder.py`

**Function**: `create_project_structure()`

**Specific Changes**:
1. **Add Template Asset Copying**: After creating empty directories, add logic to copy template assets
   - Check if plan contains `template_assets` metadata field
   - If present, copy specified folders (vendor/, css/, js/, img/) from template/ to project directory
   - Use shutil.copytree() with dirs_exist_ok=True to copy directory trees
   - Skip copying if frontend is not template-based (backend-only projects)

2. **Add Helper Function**: Create `_copy_template_assets(job_id: str, asset_list: list[str])` function
   - Takes job_id and list of asset paths to copy
   - Resolves source paths from TEMPLATE_DIR
   - Copies to project directory maintaining structure
   - Handles errors gracefully (log warnings if template files missing)

**File**: `generator.py`

**Function**: `_build_asset_context()`

**Specific Changes**:
3. **Reduce Truncation Aggressiveness**: Adjust truncation limits
   - Increase individual file limit from 6000 to 12000 characters (captures full template structure)
   - Increase total context from 32000 to 64000 characters (~16k tokens, reasonable for modern LLMs)
   - Prioritize structural files (index.html, sb-admin-2.css) over demo files

4. **Alternative: Template Reference Approach**: Instead of embedding full content, provide structural summaries
   - For large template files, extract key sections (header, sidebar, footer structure) instead of truncating mid-content
   - Include file structure metadata (available classes, IDs, data attributes) rather than full HTML
   - This requires more sophisticated parsing but provides better context

**File**: `planner.py`

**Function**: `_generate_plan_sync()` and PLANNER_SYSTEM_PROMPT

**Specific Changes**:
5. **Add Template Metadata to Plan Schema**: Update PLANNER_SYSTEM_PROMPT to include template_assets field
   - Modify example JSON output to include: `"template_assets": ["vendor/", "css/", "js/", "img/"]`
   - Instruct LLM to specify which template folders are needed based on project requirements
   - For backend-only projects, template_assets should be empty list

6. **Post-Process Plan**: In `_generate_plan_sync()`, add default template_assets if missing
   - After parsing LLM output, check if plan contains template_assets field
   - If frontend is "SB Admin 2 (Bootstrap 4)" and template_assets is missing, add default: `["vendor/", "css/", "js/", "img/"]`
   - If frontend is not template-based, ensure template_assets is empty list

7. **Validate Template Assets**: Add validation for template_assets field
   - Ensure it's a list of strings
   - Validate paths don't contain directory traversal attempts
   - Warn if specified paths don't exist in template/ directory

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bugs on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Fault Condition Checking

**Goal**: Surface counterexamples that demonstrate the bugs BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Generate a simple web application using the unfixed system, then inspect the generated project directory to verify bugs exist. Check for missing template assets, examine LLM prompts for truncation, and inspect architecture plans for missing metadata.

**Test Cases**:
1. **Missing Assets Test**: Generate "simple task dashboard" project, verify vendor/ folder is missing in generated_apps/job_xxx/ (will fail on unfixed code - folder won't exist)
2. **Truncation Test**: Add logging to generator._build_asset_context() to capture template context length, verify it's truncated to 32000 chars (will fail on unfixed code - will see truncation)
3. **Missing Metadata Test**: Generate project and inspect architecture_plan.json, verify template_assets field is missing (will fail on unfixed code - field won't exist)
4. **Backend-Only Test**: Generate "REST API only" project, verify template assets are NOT copied (should pass on unfixed code - no template needed)

**Expected Counterexamples**:
- Generated HTML files reference vendor/bootstrap/js/bootstrap.bundle.min.js but file doesn't exist
- Template context shows "... (truncated)" markers in logs
- Architecture plan JSON lacks template_assets field
- Possible causes: no copy logic in project_builder, aggressive truncation limits, planner doesn't generate metadata

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL job WHERE isBugCondition(job) DO
  result := run_pipeline_fixed(job.prompt, job.provider)
  project_dir := get_project_dir(result.job_id)
  
  ASSERT directory_exists(project_dir + "/vendor/bootstrap/")
  ASSERT directory_exists(project_dir + "/css/")
  ASSERT directory_exists(project_dir + "/js/")
  ASSERT file_exists(project_dir + "/vendor/jquery/jquery.min.js")
  
  plan := load_architecture_plan(result.job_id)
  ASSERT "template_assets" IN plan
  ASSERT plan["template_assets"] contains "vendor/"
  
  html_files := find_html_files(project_dir)
  FOR EACH html_file IN html_files DO
    referenced_assets := extract_asset_references(html_file)
    FOR EACH asset IN referenced_assets DO
      ASSERT file_exists(project_dir + "/" + asset)
    END FOR
  END FOR
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL job WHERE NOT isBugCondition(job) DO
  result_original := run_pipeline_original(job.prompt, job.provider)
  result_fixed := run_pipeline_fixed(job.prompt, job.provider)
  
  files_original := list_generated_files(result_original.job_id)
  files_fixed := list_generated_files(result_fixed.job_id)
  
  ASSERT files_original == files_fixed
  
  FOR EACH file IN files_original DO
    content_original := read_file(result_original.job_id, file)
    content_fixed := read_file(result_fixed.job_id, file)
    ASSERT content_original == content_fixed
  END FOR
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain (different project types, file structures)
- It catches edge cases that manual unit tests might miss (unusual file paths, special characters)
- It provides strong guarantees that behavior is unchanged for all non-template projects

**Test Plan**: Observe behavior on UNFIXED code first for backend-only projects, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Backend-Only Preservation**: Generate "REST API with database" project on unfixed code, capture generated files. After fix, verify identical files generated (no template assets added)
2. **Requirements.txt Preservation**: Generate multiple projects on unfixed code, verify requirements.txt content. After fix, verify identical requirements.txt generated
3. **Path Sanitization Preservation**: Test path traversal attempts (../../etc/passwd) on unfixed code, verify rejection. After fix, verify same rejection behavior
4. **Job Status Preservation**: Generate project on unfixed code, capture status transitions (pending → planning → generating → building → completed). After fix, verify identical status flow

### Unit Tests

- Test `_copy_template_assets()` function with various asset lists (vendor/, css/, js/, img/, empty list)
- Test template asset copying with missing source files (should log warning, not crash)
- Test template asset copying with invalid paths (should reject directory traversal)
- Test `_build_asset_context()` with new truncation limits (verify 12000 char limit per file, 64000 total)
- Test planner output includes template_assets field for template-based projects
- Test planner output excludes template_assets for backend-only projects
- Test architecture plan validation accepts template_assets field
- Test path sanitization continues to work after changes

### Property-Based Tests

- Generate random project prompts (varying complexity, features, tech stack) and verify template assets are copied when frontend is template-based
- Generate random backend-only prompts and verify no template assets are copied
- Generate random file lists and verify all referenced assets exist in generated projects
- Test that template context length stays within reasonable bounds across many template files
- Test that architecture plans always include template_assets field when appropriate

### Integration Tests

- Test full pipeline: prompt → planner → generator → builder for template-based web app, verify working application
- Test full pipeline for backend-only API, verify no template assets copied
- Test generated HTML files load correctly in browser (all assets resolve)
- Test switching between template-based and non-template projects in same session
- Test concurrent job generation with mixed project types (some template, some not)
- Test that generated projects can be zipped and extracted successfully with all assets intact
