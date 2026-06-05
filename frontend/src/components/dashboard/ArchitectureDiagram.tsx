import React, { useEffect, useRef, useState, useId } from 'react';
import mermaid from 'mermaid';
import { Maximize2, Minimize2, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Cyberpunk theme configuration matching the dashboard aesthetics
mermaid.initialize({
    startOnLoad: false,
    theme: 'default',
    themeVariables: {
        primaryColor: 'transparent',
        primaryTextColor: '#e2e8f0', // slate-200
        primaryBorderColor: '#06b6d4', // cyan-500
        lineColor: '#8b5cf6', // violet-500
        secondaryColor: '#0f172a', // slate-900
        tertiaryColor: '#1e293b', // slate-800
        fontFamily: 'Inter, system-ui, sans-serif',
        fontSize: '14px',
        background: 'transparent',
        nodeBorder: '#06b6d4',
        clusterBkg: 'rgba(15, 23, 42, 0.5)', // slate-900 with opacity
        clusterBorder: '#8b5cf6',
    },
    flowchart: {
        htmlLabels: true,
        curve: 'basis',
    },
    securityLevel: 'strict',
});

interface ArchitectureDiagramProps {
    chart: string;
    className?: string;
    title?: string;
}

export const ArchitectureDiagram: React.FC<ArchitectureDiagramProps> = ({
    chart,
    className = '',
    title = 'System Architecture'
}) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const fullscreenContainerRef = useRef<HTMLDivElement>(null);
    const chartId = `mermaid-${useId().replace(/:/g, '')}`;
    const [svgStr, setSvgStr] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const [isFullscreen, setIsFullscreen] = useState(false);

    useEffect(() => {
        let isMounted = true;

        const renderChart = async () => {
            try {
                setError(null);
                if (!chart) {
                    setSvgStr('');
                    return;
                }

                // Clean up the string just in case the LLM returned markdown blocks
                const cleanChart = chart.replace(/```mermaid\n?/g, '').replace(/```\n?/g, '').trim();

                // Check if syntax is valid
                await mermaid.parse(cleanChart);

                // Render to SVG string
                const renderResult = await mermaid.render(chartId, cleanChart);
                const svg = typeof renderResult === 'string' ? renderResult : renderResult.svg;

                if (isMounted) {
                    setSvgStr(svg);
                }
            } catch (err: any) {
                console.error('Mermaid rendering failed:', err);
                if (isMounted) {
                    setError(err.message || 'Failed to generate diagram');
                    setSvgStr('');
                }
            }
        };

        renderChart();

        return () => {
            isMounted = false;
        };
    }, [chart, chartId]);

    // Handle escape key to close fullscreen
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isFullscreen) {
                setIsFullscreen(false);
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isFullscreen]);

    const renderContent = (ref: React.RefObject<HTMLDivElement | null>) => {
        if (error) {
            return (
                <div className="flex flex-col items-center justify-center h-full min-h-[200px] text-red-400 p-4 border border-red-500/20 rounded-lg bg-red-500/5">
                    <AlertCircle className="w-8 h-8 mb-2 opacity-80" />
                    <p className="text-sm font-medium">Diagram Generation Failed</p>
                    <p className="text-xs opacity-70 mt-1 max-w-md text-center">
                        The generated architecture data contained invalid diagram syntax.
                    </p>
                </div>
            );
        }

        if (!svgStr) {
            return (
                <div className="flex items-center justify-center h-full min-h-[200px] text-slate-400">
                    <div className="animate-pulse">Rendering diagram...</div>
                </div>
            );
        }

        return (
            <div
                ref={ref}
                className="w-full h-full flex items-center justify-center p-4 overflow-auto mermaid-container"
                dangerouslySetInnerHTML={{ __html: svgStr }}
            />
        );
    };

    return (
        <>
            <div className={`relative group border border-slate-700/50 rounded-xl bg-slate-900/50 backdrop-blur-sm overflow-hidden flex flex-col ${className}`}>
                <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50 bg-slate-800/30">
                    <h3 className="text-sm font-medium text-slate-200">{title}</h3>

                    {svgStr && !error && (
                        <button
                            onClick={() => setIsFullscreen(true)}
                            className="p-1.5 text-slate-400 hover:text-cyan-400 hover:bg-slate-700/50 rounded-md transition-colors"
                            title="Expand Diagram"
                        >
                            <Maximize2 className="w-4 h-4" />
                        </button>
                    )}
                </div>

                <div className="flex-1 overflow-hidden relative min-h-[300px]">
                    {renderContent(containerRef)}
                </div>
            </div>

            <AnimatePresence>
                {isFullscreen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-8 bg-slate-950/90 backdrop-blur-md"
                    >
                        <motion.div
                            initial={{ scale: 0.95, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.95, opacity: 0 }}
                            transition={{ type: "spring", damping: 25, stiffness: 300 }}
                            className="relative w-full h-full max-w-7xl max-h-[90vh] bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl flex flex-col overflow-hidden"
                        >
                            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-800/80">
                                <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
                                <button
                                    onClick={() => setIsFullscreen(false)}
                                    className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors flex items-center gap-2"
                                >
                                    <span className="text-sm font-medium px-1">Close</span>
                                    <Minimize2 className="w-5 h-5" />
                                </button>
                            </div>

                            <div className="flex-1 overflow-auto p-8 bg-slate-900/50 custom-scrollbar">
                                {renderContent(fullscreenContainerRef)}
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
            <style dangerouslySetInnerHTML={{
                __html: `
        .mermaid-container svg {
          max-width: 100%;
          height: auto;
        }
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(15, 23, 42, 0.5);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(51, 65, 85, 0.8);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(71, 85, 105, 1);
        }
      `}} />
        </>
    );
};
