import { useState } from "react";
import { Link } from "react-router-dom";
import { motion, useScroll, useMotionValueEvent } from "framer-motion";
import { Button } from "../ui/Button";
import { NeutrinoLogo } from "../ui/NeutrinoLogo";
import { Menu, X } from "lucide-react";
import { cn } from "../../lib/utils";

export function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [activeTab, setActiveTab] = useState("Features");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { scrollY } = useScroll();

  useMotionValueEvent(scrollY, "change", (latest) => {
    setIsScrolled(latest > 50);
  });

  const navLinks = ["Features", "Company", "Blogs"];

  return (
    <motion.nav
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300 border-b border-transparent",
        isScrolled ? "bg-black/50 backdrop-blur-xl border-white/5 py-4" : "bg-transparent py-6"
      )}
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="container mx-auto px-6 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <NeutrinoLogo size={32} className="group-hover:drop-shadow-[0_0_12px_rgba(99,102,241,0.6)] transition-all" />
          <span className="font-clash font-bold text-xl tracking-wide text-white">Neutrino</span>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-1 bg-white/5 backdrop-blur-md px-2 py-1.5 rounded-full border border-white/5">
          {navLinks.map((link) => (
            <Link
              key={link}
              to="#"
              onClick={() => setActiveTab(link)}
              className={cn(
                "px-4 py-1.5 rounded-full text-sm font-medium transition-all relative",
                activeTab === link ? "text-white" : "text-zinc-400 hover:text-white"
              )}
            >
              {activeTab === link && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute inset-0 bg-white/10 rounded-full"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
              <span className="relative z-10">{link}</span>
            </Link>
          ))}
        </div>

        {/* Right Actions */}
        <div className="hidden md:flex items-center gap-4">
          <Link to="/login" className="text-sm font-medium text-zinc-300 hover:text-white transition-colors">
            Sign in
          </Link>
          <Link to="/dashboard">
            <Button variant="primary" size="sm" className="rounded-full px-6">
              Get Started
            </Button>
          </Link>
        </div>

        {/* Mobile Menu Toggle */}
        <button
          className="md:hidden text-zinc-300 hover:text-white"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        >
          {mobileMenuOpen ? <X /> : <Menu />}
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="md:hidden bg-black/90 backdrop-blur-xl border-b border-white/10 overflow-hidden"
        >
          <div className="container mx-auto px-6 py-8 flex flex-col gap-6">
            {navLinks.map((link) => (
              <Link
                key={link}
                to="#"
                className="text-lg font-medium text-zinc-300 hover:text-white"
                onClick={() => setMobileMenuOpen(false)}
              >
                {link}
              </Link>
            ))}
            <div className="h-px bg-white/10 w-full" />
            <Link to="/login" className="text-lg font-medium text-zinc-300 hover:text-white">
              Sign in
            </Link>
            <Link to="/dashboard" className="w-full block">
              <Button variant="primary" className="w-full">
                Get Started
              </Button>
            </Link>
          </div>
        </motion.div>
      )}
    </motion.nav>
  );
}
