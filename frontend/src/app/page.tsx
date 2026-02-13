"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { BarChart, DonutChart, AreaChart } from "@tremor/react";
import ReactMarkdown from "react-markdown";

// Types
interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  data?: Record<string, unknown>[];
  columns?: string[];
  visualization?: "none" | "table" | "bar_chart" | "line_chart" | "pie_chart";
  chart_config?: {
    x?: string;
    y?: string;
    title?: string;
  };
  sql?: string;
  row_count?: number;
  isLoading?: boolean;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [hasStartedChat, setHasStartedChat] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const sendMessage = async (messageText?: string) => {
    const text = messageText || input;
    if (!text.trim() || isLoading) return;

    setHasStartedChat(true);

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: text,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    const loadingId = (Date.now() + 1).toString();
    setMessages((prev) => [
      ...prev,
      {
        id: loadingId,
        role: "assistant",
        content: "Analizez întrebarea...",
        isLoading: true,
      },
    ]);

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      const data = await response.json();

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === loadingId
            ? {
              ...msg,
              content: data.text.replace(/\\n/g, '\n'),
              data: data.data,
              columns: data.columns,
              visualization: data.visualization,
              chart_config: data.chart_config,
              sql: data.sql,
              row_count: data.row_count,
              isLoading: false,
            }
            : msg
        )
      );
    } catch {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === loadingId
            ? {
              ...msg,
              content: "Eroare la conectarea cu serverul.",
              isLoading: false,
            }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const formatValue = (val: unknown): string => {
    if (val === null || val === undefined) return "-";
    if (typeof val === "number") {
      return val.toLocaleString("ro-RO", { maximumFractionDigits: 2 });
    }
    return String(val);
  };

  // Format column headers nicely (remove underscores, capitalize)
  const formatColumnHeader = (col: string): string => {
    return col
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase())
      .replace('Numar', 'Număr')
      .replace('Valoare', 'Valoare')
      .replace('Reclamatii', 'Reclamații')
      .replace('Totala', 'Totală');
  };

  // Warm color palette for charts (matching reference images)
  const chartColors = [
    "#F59E0B", // Amber-500 (warm orange-yellow, primary)
    "#EF4444", // Red-500
    "#10B981", // Emerald-500
    "#3B82F6", // Blue-500
    "#8B5CF6", // Violet-500
    "#EC4899", // Pink-500
    "#14B8A6", // Teal-500
    "#F97316", // Orange-500
  ];

  // KPI Card component for single-value responses
  const renderKpiCard = (data: Record<string, unknown>[], columns: string[], title?: string) => {
    if (!data[0] || !columns[0]) return null;
    const value = data[0][columns[columns.length > 1 ? 1 : 0]];
    const label = columns.length > 1 ? String(data[0][columns[0]]) : formatColumnHeader(columns[0]);
    const numericValue = typeof value === "number" ? value : parseFloat(String(value));

    return (
      <div className="mt-4 p-6 rounded-2xl bg-card border border-border/50 shadow-sm transition-all hover:bg-accent/5">
        {title && (
          <p className="text-muted-foreground text-sm font-medium mb-1">{title}</p>
        )}
        <div className="flex items-baseline gap-2">
          <span className="text-4xl font-bold font-outfit text-foreground">
            {!isNaN(numericValue) ? numericValue.toLocaleString("ro-RO") : String(value)}
          </span>
        </div>
        <p className="text-muted-foreground text-sm mt-1">{label}</p>
      </div>
    );
  };

  const renderVisualization = (msg: ChatMessage) => {
    if (!msg.data || msg.data.length === 0) return null;

    const { visualization, data, columns, chart_config } = msg;

    // ── KPI CARD: single-value responses ──
    if (visualization === "none" && data.length === 1 && columns && columns.length <= 2) {
      return renderKpiCard(data, columns, chart_config?.title);
    }

    // ── TABLE: small datasets, rankings, detailed results ──
    if (visualization === "table" || (!visualization && data.length <= 15) || visualization === "none") {
      if (data.length > 0 && columns && columns.length > 0) {
        return (
          <div className="mt-4 rounded-2xl overflow-hidden bg-card border border-border/50 shadow-sm">
            {chart_config?.title && (
              <div className="px-5 py-3 border-b border-border/50 bg-muted/20">
                <h4 className="text-foreground font-semibold text-sm">{chart_config.title}</h4>
              </div>
            )}
            <Table>
              <TableHeader>
                <TableRow className="border-border/50 hover:bg-muted/50">
                  {columns.map((col) => (
                    <TableHead key={col} className="text-muted-foreground font-medium text-xs uppercase tracking-wider">
                      {formatColumnHeader(col)}
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.slice(0, 20).map((row, i) => (
                  <TableRow key={i} className="border-border/50 hover:bg-muted/50 transition-colors">
                    {columns.map((col, ci) => (
                      <TableCell key={col} className={`text-foreground/90 ${ci === 0 ? "font-medium text-foreground" : ""}`}>
                        {typeof row[col] === "number" ? (
                          <span className="font-semibold text-foreground">
                            {formatValue(row[col])}
                          </span>
                        ) : (
                          formatValue(row[col])
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {data.length > 20 && (
              <p className="text-sm text-muted-foreground p-3 text-center border-t border-border/50">
                Afișând primele 20 din {data.length} rânduri
              </p>
            )}
          </div>
        );
      }
    }

    // ── BAR CHART: categorical data, monthly breakdowns ──
    if (visualization === "bar_chart" && columns && columns.length >= 2) {
      const xKey = chart_config?.x || columns[0];
      const yKey = chart_config?.y || columns[1];
      const chartTitle = chart_config?.title;
      const chartData = data.slice(0, 15).map((item) => ({
        ...item,
        [xKey]: String(item[xKey]).slice(0, 15),
      }));

      return (
        <div className="mt-4 p-6 rounded-2xl bg-card border border-border/50 shadow-sm">
          {chartTitle && (
            <div className="mb-4">
              <h4 className="text-foreground font-semibold text-base">{chartTitle}</h4>
            </div>
          )}
          <BarChart
            data={chartData as Record<string, string | number>[]}
            index={xKey}
            categories={[yKey]}
            colors={["amber"]}
            className="h-72"
            showAnimation
            yAxisWidth={70}
            showLegend={false}
            valueFormatter={(v) => v.toLocaleString("ro-RO")}
          />
          <div className="mt-3 flex items-center gap-2 justify-center">
            <div className="w-3 h-3 rounded-sm bg-primary" />
            <span className="text-muted-foreground text-xs">{formatColumnHeader(yKey)}</span>
          </div>
        </div>
      );
    }

    // ── PIE/DONUT CHART: distribution, proportions ──
    if (visualization === "pie_chart" && columns && columns.length >= 2) {
      const nameKey = chart_config?.x || columns[0];
      const valueKey = chart_config?.y || columns[1];
      const chartTitle = chart_config?.title;
      const chartData = data.slice(0, 8);

      return (
        <div className="mt-4 p-6 rounded-2xl bg-card border border-border/50 shadow-sm">
          {chartTitle && (
            <div className="mb-4">
              <h4 className="text-foreground font-semibold text-base">{chartTitle}</h4>
            </div>
          )}
          <DonutChart
            data={chartData as Record<string, string | number>[]}
            index={nameKey}
            category={valueKey}
            colors={["amber", "red", "emerald", "blue", "violet", "pink", "teal", "orange"]}
            className="h-64"
            showAnimation
            showLabel={false}
            valueFormatter={(v) => v.toLocaleString("ro-RO")}
          />
          <div className="mt-4 flex flex-wrap gap-3 justify-center">
            {chartData.map((item, i) => (
              <div key={i} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: chartColors[i % chartColors.length] }}
                />
                <span className="text-muted-foreground text-xs">
                  {String(item[nameKey]).slice(0, 22)}
                </span>
              </div>
            ))}
          </div>
        </div>
      );
    }

    // ── LINE/AREA CHART: time-series trends ──
    if (visualization === "line_chart" && columns && columns.length >= 2) {
      const xKey = chart_config?.x || columns[0];
      const yKey = chart_config?.y || columns[1];
      const chartTitle = chart_config?.title;

      return (
        <div className="mt-4 p-6 rounded-2xl bg-card border border-border/50 shadow-sm">
          {chartTitle && (
            <div className="mb-4">
              <h4 className="text-foreground font-semibold text-base">{chartTitle}</h4>
            </div>
          )}
          <AreaChart
            data={data.slice(0, 24) as Record<string, string | number>[]}
            index={xKey}
            categories={[yKey]}
            colors={["blue"]}
            className="h-72"
            showAnimation
            yAxisWidth={65}
            curveType="natural"
            showGradient={true}
            valueFormatter={(v) => v.toLocaleString("ro-RO")}
          />
          <div className="mt-3 flex items-center gap-2 justify-center">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            <span className="text-muted-foreground text-xs">{formatColumnHeader(yKey)}</span>
          </div>
        </div>
      );
    }

    return null;
  };

  const suggestedQuestions = [
    { icon: "✨", text: "Reclamații în 2024" },
    { icon: "📊", text: "Top furnizori" },
    { icon: "🔍", text: "Motive principale" },
    { icon: "👤", text: "PM cu cele mai multe reclamații" },
  ];

  // Sparkle icon component
  const SparkleIcon = () => (
    <svg className="w-6 h-6 text-primary" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0L14.59 9.41L24 12L14.59 14.59L12 24L9.41 14.59L0 12L9.41 9.41L12 0Z" />
    </svg>
  );

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-300">
      {/* Header */}
      <header className="border-b border-border/40 bg-background/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          {/* Logo - Clickable to reset */}
          <div
            className="cursor-pointer hover:opacity-80 transition group"
            onClick={() => {
              setHasStartedChat(false);
              setMessages([]);
              setInput("");
            }}
          >
            <span className="font-outfit font-bold text-xl md:text-2xl tracking-tighter text-foreground">
              MOBEXPERT <span className="text-primary font-extrabold group-hover:text-primary/80 transition-colors">AI</span>
            </span>
          </div>

          {/* User avatar */}
          <div className="w-9 h-9 rounded-full bg-accent flex items-center justify-center border border-border/50">
            <svg className="w-5 h-5 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-3xl mx-auto px-4 py-8">
        {!hasStartedChat ? (
          /* Welcome State */
          <div className="flex flex-col items-center pt-24 animate-in fade-in duration-700 slide-in-from-bottom-4">

            {/* Greeting */}
            <h1 className="font-playfair font-medium text-7xl md:text-9xl text-stone-800 mb-6 text-center tracking-tight leading-tight">
              Bună ziua
            </h1>

            {/* Subtitle */}
            <p className="text-muted-foreground text-center max-w-md mb-12 text-lg font-light">
              Asistentul tău inteligent pentru analiza reclamațiilor.
            </p>

            {/* Suggestion chips */}
            <div className="flex flex-wrap gap-3 justify-center mb-12">
              {suggestedQuestions.map((q, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(q.text)}
                  className="flex items-center gap-2 px-5 py-3 rounded-full border border-border/40 bg-card hover:bg-accent/50 hover:border-primary/50 text-foreground hover:text-primary transition-all shadow-lg hover:shadow-primary/10 group"
                >
                  <span className="group-hover:scale-110 transition-transform">{q.icon}</span>
                  <span className="text-sm font-medium">{q.text}</span>
                </button>
              ))}
            </div>

            {/* Input */}
            <div className="w-full max-w-xl">
              <div className="relative group">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-primary/30 to-purple-600/30 rounded-full blur opacity-50 group-hover:opacity-100 transition duration-1000"></div>
                <div className="relative">
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                    placeholder="Scrie întrebarea ta..."
                    className="w-full h-14 pl-6 pr-14 rounded-full border-stone-200 bg-white/80 text-stone-800 placeholder:text-stone-400 focus:border-primary/50 focus:ring-primary/20 shadow-xl shadow-orange-100/50 backdrop-blur-xl"
                  />
                  <Button
                    onClick={() => sendMessage()}
                    disabled={isLoading || !input.trim()}
                    className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 hover:scale-105 transition-all shadow-lg disabled:opacity-50 disabled:hover:scale-100"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                    </svg>
                  </Button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Chat State */
          <div className="flex flex-col min-h-[calc(100vh-180px)]">
            {/* Chat Header */}
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-stone-200">
              <div className="flex items-center gap-3">
                <div
                  className="cursor-pointer hover:opacity-80 transition"
                  onClick={() => { setMessages([]); setHasStartedChat(false); }}
                >
                  <span className="font-outfit font-bold text-xl text-foreground tracking-tighter">
                    MOBEXPERT <span className="text-primary font-extrabold">AI</span>
                  </span>
                </div>
              </div>
              <button
                onClick={() => { setMessages([]); setHasStartedChat(false); }}
                className="text-stone-500 hover:text-stone-700 text-sm transition flex items-center gap-1"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Conversație nouă
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto space-y-6 pb-6 scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  {/* AI Avatar for assistant messages */}
                  {msg.role === "assistant" && (
                    <div className="mr-4 flex-shrink-0 mt-1">
                      <div className="w-8 h-8 rounded-lg bg-[#ea580c] flex items-center justify-center shadow-md">
                        <span className="font-outfit font-bold text-white text-xl pb-1">m</span>
                      </div>
                    </div>
                  )}

                  <div
                    className={`rounded-2xl px-6 py-5 shadow-sm border ${msg.role === "user"
                      ? "max-w-[85%] bg-primary text-primary-foreground border-primary/20"
                      : "max-w-[90%] bg-white text-stone-800 border-stone-100"
                      }`}
                  >
                    {msg.isLoading ? (
                      <div className="flex items-center gap-3">
                        <div className="flex gap-1.5 h-full items-center">
                          <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                          <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                          <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                        </div>
                        <span className="text-muted-foreground text-sm font-medium animate-pulse">Procesez datele...</span>
                      </div>
                    ) : (
                      <>
                        {/* Text Content */}
                        <div className="prose prose-stone prose-sm max-w-none font-lora">
                          <ReactMarkdown
                            components={{
                              p: ({ children }) => <p className={`mb-3 last:mb-0 ${msg.role === "user" ? "text-white/95" : "text-stone-700"} leading-relaxed`}>{children}</p>,
                              strong: ({ children }) => <strong className={`${msg.role === "user" ? "text-white" : "text-primary"} font-bold`}>{children}</strong>,
                              ul: ({ children }) => <ul className="list-none space-y-2 my-2">{children}</ul>,
                              li: ({ children }) => (
                                <li className="flex gap-2 items-start">
                                  <span className={`${msg.role === "user" ? "text-white/60" : "text-primary"} mt-1.5 text-xs`}>●</span>
                                  <span>{children}</span>
                                </li>
                              ),
                              h1: ({ children }) => <h1 className="text-lg font-bold mb-2 font-playfair">{children}</h1>,
                              h2: ({ children }) => <h2 className="text-base font-semibold mb-2 font-playfair">{children}</h2>,
                              code: ({ children }) => <code className="bg-stone-100 px-1 py-0.5 rounded text-xs font-mono text-stone-600">{children}</code>
                            }}
                          >
                            {msg.content}
                          </ReactMarkdown>
                        </div>

                        {/* Viz Render */}
                        {msg.data && msg.data.length > 0 && (
                          <div className="mt-4 animate-in fade-in zoom-in-95 duration-500">
                            {renderVisualization(msg)}
                          </div>
                        )}
                      </>
                    )}
                  </div>

                  {/* User avatar */}
                  {msg.role === "user" && (
                    <div className="w-9 h-9 rounded-full bg-accent flex items-center justify-center ml-3 flex-shrink-0 mt-1 border border-border/50">
                      <svg className="w-5 h-5 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                  )}
                </div>
              ))}
              <div ref={scrollRef} />
            </div>

            {/* Input at bottom */}
            <div className="sticky bottom-0 bg-white/80 backdrop-blur-md pt-4 pb-4 border-t border-stone-200/50">
              <div className="relative max-w-4xl mx-auto px-4">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                  placeholder="Scrie mesajul tău..."
                  disabled={isLoading}
                  className="w-full h-14 pl-6 pr-14 rounded-full border-stone-200 bg-white/80 text-stone-800 placeholder:text-stone-400 focus:border-primary/50 focus:ring-primary/20 shadow-lg backdrop-blur-md transition-all"
                />
                <Button
                  onClick={() => sendMessage()}
                  disabled={isLoading || !input.trim()}
                  className="absolute right-6 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 hover:scale-105 transition-all shadow-md disabled:opacity-50"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                  </svg>
                </Button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
