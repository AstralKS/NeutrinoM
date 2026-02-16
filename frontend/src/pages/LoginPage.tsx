import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthProvider";
import { Navbar } from "../components/layout/Navbar";
import { Footer } from "../components/layout/Footer";
import { GlassCard } from "../components/ui/GlassCard";
import { Button } from "../components/ui/Button";
import { Github, Chrome, Shield, Zap } from "lucide-react";
import { motion } from "framer-motion";

export function LoginPage() {
  const { user, loading, signInWithGoogle, signInWithGithub } = useAuth();
  const navigate = useNavigate();

  // Redirect to dashboard if already logged in
  useEffect(() => {
    if (user && !loading) {
      navigate("/dashboard", { replace: true });
    }
  }, [user, loading, navigate]);

  return (
    <div className="bg-black min-h-screen text-white flex flex-col items-center justify-center relative overflow-hidden">
      <Navbar />

      <div className="container relative z-10 px-6 flex items-center justify-center min-h-[80vh]">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="w-full max-w-md"
        >
          <GlassCard className="p-10 text-center" variant="heavy">
            {/* Logo / Header */}
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.5 }}
              className="mb-8"
            >
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center mx-auto mb-5 shadow-lg shadow-indigo-500/25">
                <Shield className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-3xl font-clash font-bold mb-2">Welcome Back</h1>
              <p className="text-zinc-400 text-sm leading-relaxed">
                Sign in to access your AI-powered repository insights and saved analyses.
              </p>
            </motion.div>

            {/* OAuth Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.4 }}
              className="space-y-3"
            >
              <Button
                className="w-full gap-3 justify-center"
                variant="primary"
                size="lg"
                onClick={signInWithGithub}
              >
                <Github className="w-5 h-5" />
                Continue with GitHub
              </Button>

              <Button
                className="w-full gap-3 justify-center"
                variant="outline"
                size="lg"
                onClick={signInWithGoogle}
              >
                <Chrome className="w-5 h-5" />
                Continue with Google
              </Button>
            </motion.div>

            {/* Trust signals */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6, duration: 0.5 }}
              className="mt-8 pt-6 border-t border-white/5"
            >
              <div className="flex items-center justify-center gap-2 text-xs text-zinc-500">
                <Zap className="w-3 h-3" />
                <span>Secure OAuth 2.0 authentication</span>
              </div>
            </motion.div>
          </GlassCard>
        </motion.div>
      </div>

      {/* Background Effects */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-600/8 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-cyan-600/5 rounded-full blur-[100px] pointer-events-none" />

      <Footer />
    </div>
  );
}
