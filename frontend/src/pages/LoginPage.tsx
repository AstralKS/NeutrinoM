import { useState } from "react";
import { Navigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Github, Loader2, UserCheck } from "lucide-react";
import { supabase } from "../services/supabase";
import { useAuth } from "../contexts/AuthProvider";
import { NeutrinoLogo } from "../components/ui/NeutrinoLogo";
import { GlassCard } from "../components/ui/GlassCard";

export default function LoginPage() {
  const { user, loading, signInWithEmail } = useAuth();
  const [isLoggingIn, setIsLoggingIn] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex flex-col pt-24 items-center justify-center text-white">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // Already logged in
  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleOAuthLogin = async (provider: "github" | "google") => {
    try {
      setIsLoggingIn(provider);
      setError(null);

      const { error } = await supabase.auth.signInWithOAuth({
        provider,
        options: {
          // GitHub specifically requires these scopes to read repos
          scopes: provider === 'github' ? 'repo read:user user:email' : undefined,
          redirectTo: `${window.location.origin}/dashboard`
        }
      });

      if (error) throw error;

    } catch (err: any) {
      console.error("Login error:", err);
      setError(err.message || "Failed to sign in. Please try again.");
      setIsLoggingIn(null);
    }
  };

  const handleDemoLogin = async () => {
    try {
      setIsLoggingIn("demo");
      setError(null);
      await signInWithEmail("judge@neutrino.dev", "Demo2026!");
      // On success, the AuthProvider session listener will update state,
      // which triggers the <Navigate> up top automatically.
    } catch (err: any) {
      console.error("Demo login error:", err);
      // More specific wording if demo fails (e.g. account deleted)
      setError("Demo account unavailable. It may have been modified or deleted. Please use Google/GitHub.");
      setIsLoggingIn(null);
    }
  };

  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Background gradients */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md relative z-10"
      >
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center mb-6 shadow-[0_0_30px_rgba(99,102,241,0.2)] border border-white/10">
            <NeutrinoLogo size={40} className="drop-shadow-[0_0_12px_rgba(99,102,241,0.6)]" />
          </div>
          <h1 className="text-3xl font-bold font-clash text-white text-center mb-2">
            Welcome to Neutrino
          </h1>
          <p className="text-zinc-400 text-center">
            Sign in to start analyzing your codebase and generating executive reports.
          </p>
        </div>

        <GlassCard className="p-8">
          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm text-center">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <button
              onClick={() => handleOAuthLogin("github")}
              disabled={isLoggingIn !== null}
              className="w-full relative flex items-center justify-center gap-3 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 text-white p-4 rounded-xl font-medium transition-all group disabled:opacity-50 hover:shadow-[0_0_20px_rgba(255,255,255,0.05)]"
            >
              {isLoggingIn === "github" ? (
                <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
              ) : (
                <>
                  <Github className="w-5 h-5 group-hover:scale-110 transition-transform" />
                  Continue with GitHub
                </>
              )}
            </button>

            <button
              onClick={() => handleOAuthLogin("google")}
              disabled={isLoggingIn !== null}
              className="w-full relative flex items-center justify-center gap-3 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 text-white p-4 rounded-xl font-medium transition-all group disabled:opacity-50 hover:shadow-[0_0_20px_rgba(255,255,255,0.05)]"
            >
              {isLoggingIn === "google" ? (
                <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
              ) : (
                <>
                  <svg className="w-5 h-5 group-hover:scale-110 transition-transform" viewBox="0 0 24 24">
                    <path
                      fill="currentColor"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="currentColor"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                  Continue with Google
                </>
              )}
            </button>
          </div>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/10" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-[#0f0f13] px-3 text-zinc-500 font-medium">
                Or
              </span>
            </div>
          </div>

          <button
            onClick={handleDemoLogin}
            disabled={isLoggingIn !== null}
            className="w-full relative flex items-center justify-center gap-3 bg-indigo-600 hover:bg-indigo-500 text-white p-4 rounded-xl font-medium transition-all group disabled:opacity-50 hover:shadow-[0_0_20px_rgba(99,102,241,0.3)] shadow-[0_0_10px_rgba(99,102,241,0.15)]"
          >
            {isLoggingIn === "demo" ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin text-white/70" />
                Logging in...
              </>
            ) : (
              <>
                <UserCheck className="w-5 h-5 group-hover:scale-110 transition-transform" />
                Log in as Guest Judge
              </>
            )}
          </button>

          <div className="mt-8 pt-6 border-t border-white/5 text-center px-4">
            <p className="text-xs text-zinc-500 leading-relaxed">
              By signing in, you agree to Neutrino's{" "}
              <a href="#" className="text-zinc-400 hover:text-white underline underline-offset-2 decoration-white/20 transition-colors">Terms of Service</a>
              {" "}and{" "}
              <a href="#" className="text-zinc-400 hover:text-white underline underline-offset-2 decoration-white/20 transition-colors">Privacy Policy</a>.
            </p>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  );
}
