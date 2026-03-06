# Bugfix Requirements Document

## Introduction

The multi-agent code generation system (orchestrator, planner, generator) is not properly utilizing the SB Admin 2 template structure when generating web applications. The system consists of three components:

- **Planner**: Generates architecture plans with file lists and tech stack decisions
- **Generator**: Generates code for each file using LLM with template context
- **Orchestrator**: Coordinates the pipeline and manages job lifecycle

The bugs prevent generated applications from functioning correctly because:
1. Template asset files (vendor libraries, CSS, JS) are not copied to generated projects
2. Template context is heavily truncated before being sent to the LLM
3. The planner doesn't communicate template structure requirements to the generator

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the project_builder creates a project structure THEN the system only creates empty directories and writes generated code files without copying template assets from the template/ folder

1.2 WHEN the generator loads template context in _build_asset_context() THEN the system truncates template files to 6000 characters and limits total context to 32000 characters, causing incomplete template information to reach the LLM

1.3 WHEN the planner generates an architecture plan THEN the system does not include template file structure information or specify which template assets should be copied versus generated

1.4 WHEN generated HTML files reference template assets like vendor/bootstrap/js/bootstrap.bundle.min.js THEN these files do not exist in the generated project directory, causing broken references

1.5 WHEN the generator receives truncated template context THEN the LLM cannot properly adapt the template structure, resulting in incomplete or incorrect code generation

### Expected Behavior (Correct)

2.1 WHEN the project_builder creates a project structure THEN the system SHALL copy all necessary template assets (vendor/, css/, js/, img/ folders) from the template/ directory to the generated project

2.2 WHEN the generator loads template context THEN the system SHALL provide sufficient template information to the LLM without excessive truncation, or use a template reference approach instead of embedding full content

2.3 WHEN the planner generates an architecture plan THEN the system SHALL include template structure metadata specifying which template assets to copy and which files to generate

2.4 WHEN generated HTML files reference template assets THEN these files SHALL exist in the generated project directory at the correct paths

2.5 WHEN the generator provides template context to the LLM THEN the system SHALL ensure the LLM receives complete structural information needed to properly adapt the template

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the orchestrator coordinates the pipeline (prompt → planner → generator → file builder) THEN the system SHALL CONTINUE TO execute steps in the correct order with proper status tracking

3.2 WHEN the generator creates code for non-template files (backend Python files, requirements.txt, database.py) THEN the system SHALL CONTINUE TO generate these files correctly without template context

3.3 WHEN the project_builder sanitizes file paths THEN the system SHALL CONTINUE TO prevent directory traversal attacks and maintain security

3.4 WHEN the system handles multiple concurrent jobs THEN the system SHALL CONTINUE TO isolate job data and maintain separate project directories

3.5 WHEN the planner validates architecture plans THEN the system SHALL CONTINUE TO ensure required fields (project_name, files list) are present

3.6 WHEN the generator strips markdown fences from LLM output THEN the system SHALL CONTINUE TO clean code output correctly
