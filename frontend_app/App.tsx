import React, { Suspense, lazy } from 'react';
import '@radix-ui/themes/styles.css';
import { Theme } from '@radix-ui/themes';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import './styles.css';

import Home from './src/pages/Home';
import NotFound from './src/pages/NotFound';

const Builder = lazy(() => import('./src/pages/Builder'));
const HowItWorks = lazy(() => import('./src/pages/HowItWorks'));
const Examples = lazy(() => import('./src/pages/Examples'));
const Pricing = lazy(() => import('./src/pages/Pricing'));

const App: React.FC = () => {
  return (
    <Theme appearance="dark" radius="large" scaling="100%">
      <Router>
        <Suspense
          fallback={
            <div className="min-h-screen bg-forge-dark flex items-center justify-center">
              <div className="w-8 h-8 rounded-full border-2 border-forge-accent border-t-transparent animate-spin" />
            </div>
          }
        >
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/builder" element={<Builder />} />
            <Route path="/how-it-works" element={<HowItWorks />} />
            <Route path="/examples" element={<Examples />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
        <ToastContainer
          position="bottom-right"
          autoClose={3000}
          newestOnTop
          closeOnClick
          pauseOnHover
          theme="dark"
        />
      </Router>
    </Theme>
  );
};

export default App;