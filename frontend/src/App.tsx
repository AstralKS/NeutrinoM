import { useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { Navbar } from "./components/layout/Navbar";
import { Hero } from "./components/features/Hero";
import { FeaturesSection } from "./components/features/FeaturesSection";
import { DashboardPreviewSection } from "./components/features/DashboardPreviewSection";
import { Footer } from "./components/layout/Footer";
import { DashboardPage } from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import { AuthProvider, useAuth } from "./contexts/AuthProvider";
import { AnalysisService } from "./services/api";

function LandingPage() {
  return (
    <div className="bg-black min-h-screen text-white selection:bg-indigo-500/30">
      <Navbar />
      <Hero />
      <FeaturesSection />
      <DashboardPreviewSection />
      <Footer />
    </div>
  );
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex flex-col pt-24 px-6 items-center justify-center text-white">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-zinc-400">Verifying session...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function AppRoutes() {
  // Wake up backend on initial load (Render free tier sleeps after inactivity)
  useEffect(() => {
    AnalysisService.checkHealth().catch(() => {
      // Ignore errors - this is just a best-effort wake-up ping
    });
  }, []);

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
}

export default App;
