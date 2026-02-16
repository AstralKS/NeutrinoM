import { useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthProvider";
import { Navbar } from "./components/layout/Navbar";
import { Hero } from "./components/features/Hero";
import { FeaturesSection } from "./components/features/FeaturesSection";
import { DashboardPreviewSection } from "./components/features/DashboardPreviewSection";
import { Footer } from "./components/layout/Footer";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
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

/**
 * Handles the OAuth callback redirect from Supabase.
 * Supabase appends #access_token=... to the URL on redirect.
 * The Supabase client automatically picks this up via detectSessionInUrl.
 */
function AuthCallback() {
  const navigate = useNavigate();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading) {
      if (user) {
        navigate("/dashboard", { replace: true });
      } else {
        navigate("/login", { replace: true });
      }
    }
  }, [user, loading, navigate]);

  return (
    <div className="bg-black min-h-screen text-white flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-zinc-400 text-sm">Completing sign in...</p>
      </div>
    </div>
  );
}

/**
 * Wrapper that redirects to /login if the user isn't authenticated.
 */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="bg-black min-h-screen text-white flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
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
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}

export default App;
