import { Github, Twitter, Linkedin } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-black border-t border-white/10 py-12">
      <div className="container mx-auto px-6">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold">N</div>
            <span className="font-clash font-bold text-xl text-white">Neutrino</span>
          </div>
          
          <div className="flex gap-8 text-zinc-400 text-sm">
            <a href="#" className="hover:text-white transition-colors">Privacy</a>
            <a href="#" className="hover:text-white transition-colors">Terms</a>
            <a href="#" className="hover:text-white transition-colors">Contact</a>
          </div>

          <div className="flex gap-4">
            <a href="#" className="text-zinc-400 hover:text-white transition-colors"><Github className="w-5 h-5" /></a>
            <a href="#" className="text-zinc-400 hover:text-white transition-colors"><Twitter className="w-5 h-5" /></a>
            <a href="#" className="text-zinc-400 hover:text-white transition-colors"><Linkedin className="w-5 h-5" /></a>
          </div>
        </div>
        <div className="mt-8 text-center text-zinc-600 text-xs">
          © {new Date().getFullYear()} Neutrino AI. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
