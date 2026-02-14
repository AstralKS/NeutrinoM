
import { Navbar } from "../components/layout/Navbar";
import { Footer } from "../components/layout/Footer";
import { GlassCard } from "../components/ui/GlassCard";
import { Button } from "../components/ui/Button";

export function LoginPage() {
  return (
    <div className="bg-black min-h-screen text-white flex flex-col items-center justify-center relative overflow-hidden">
      <Navbar />
      
      <div className="container relative z-10 px-6">
        <GlassCard className="max-w-md mx-auto p-8 text-center" variant="heavy">
          <h1 className="text-3xl font-clash font-bold mb-4">Sign In</h1>
          <p className="text-zinc-400 mb-8">
            Access your personalized dashboard and saved analyses.
          </p>
          
          <div className="space-y-4">
             <Button className="w-full" variant="primary">
               Sign in with GitHub
             </Button>
             <Button className="w-full" variant="outline">
               Sign in with Email
             </Button>
          </div>
          
          <div className="mt-6 text-sm text-zinc-500">
            Don't have an account? <a href="#" className="text-white hover:underline">Sign up</a>
          </div>
        </GlassCard>
      </div>

      {/* Background Effect */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[100px] pointer-events-none" />
      
      <Footer />
    </div>
  );
}
