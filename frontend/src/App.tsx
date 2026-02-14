import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Navbar } from "./components/layout/Navbar";
import { Hero } from "./components/features/Hero";
import { FeaturesSection } from "./components/features/FeaturesSection";
import { DashboardPreviewSection } from "./components/features/DashboardPreviewSection";
import { Footer } from "./components/layout/Footer";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";

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

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </Router>
  );
}

export default App;
