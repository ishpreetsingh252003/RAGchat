"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  Bot,
  User,
  Loader2,
  AlertTriangle,
  ExternalLink,
  History,
  ArrowLeftRight,
  HelpCircle,
  LogOut,
  Sparkles,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  Copy,
  ShieldCheck,
} from "lucide-react";
import { sendMessage, ChatResponse } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: ChatResponse;
}

const EXAMPLE_QUESTIONS = [
  "What is an Expense Ratio?",
  "Compare Index vs Active Funds",
  "Explain Exit Load",
];

const SIDEBAR_ITEMS = [
  { icon: MessageSquare, label: "New Chat", active: true, onClick: "newChat" },
  { icon: History, label: "Chat History", onClick: "chatHistory" },
  { icon: ArrowLeftRight, label: "Compare Funds" },
];

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSend = async (question?: string) => {
    const text = (question ?? input).trim();
    if (!text || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: { answer_sentences: [text] },
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await sendMessage(text);
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response,
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: {
          grounded: false,
          answer_sentences: [
            error instanceof Error
              ? error.message
              : "An unexpected error occurred. Please try again.",
          ],
        },
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-screen bg-background text-on-surface overflow-hidden">
      {/* Sidebar */}
      <aside className="hidden md:flex w-64 flex-col border-r border-outline-variant bg-surface-container-low">
        {/* Logo */}
        <div className="p-4 border-b border-outline-variant">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-emerald flex items-center justify-center">
              <Bot className="w-5 h-5 text-surface-container-lowest" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-on-surface">FAQ Assistant</h2>
              <p className="text-xs text-on-surface-variant">Verified Facts Only</p>
            </div>
          </div>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            onClick={() => setMessages([])}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald hover:bg-emerald/90 text-surface-container-lowest font-medium text-sm transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            New Chat
          </button>
        </div>

        {/* Nav Items */}
        <nav className="flex-1 px-2 space-y-1">
          {SIDEBAR_ITEMS.map((item) => (
            <button
              key={item.label}
              onClick={() => {
                if (item.onClick === "newChat") {
                  setMessages([]);
                } else if (item.onClick === "chatHistory") {
                  alert("Chat history feature coming soon!");
                }
              }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                item.active
                  ? "bg-surface-container-high text-on-surface"
                  : "text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
              }`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </button>
          ))}
        </nav>

        {/* Pro Banner */}
        <div className="mx-3 mb-3 p-3 rounded-xl bg-surface-container border border-outline-variant">
          <p className="text-xs text-on-surface-variant mb-2">
            Pro Members get access to unlimited real-time SEBI feeds.
          </p>
          <button className="w-full py-1.5 px-3 rounded-lg border border-emerald text-emerald text-xs font-medium hover:bg-emerald/10 transition-colors">
            Upgrade to Pro
          </button>
        </div>

        {/* Bottom Actions */}
        <div className="p-2 border-t border-outline-variant space-y-1">
          <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors">
            <HelpCircle className="w-4 h-4" />
            Help Center
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors">
            <LogOut className="w-4 h-4" />
            Log Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-3 border-b border-outline-variant bg-surface-container-low">
          <div className="flex items-center gap-6">
            <h1 className="text-lg font-semibold text-on-surface">Mutual Fund FAQ Assistant</h1>
            <nav className="hidden lg:flex items-center gap-4">
              {["Guidelines", "Methodology", "API"].map((item) => (
                <button
                  key={item}
                  className="text-sm text-on-surface-variant hover:text-primary transition-colors"
                >
                  {item}
                </button>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <button className="p-2 rounded-lg text-on-surface-variant hover:bg-surface-container transition-colors">
              <HelpCircle className="w-5 h-5" />
            </button>
            <button
              onClick={() => setMessages([])}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald hover:bg-emerald/90 text-surface-container-lowest text-sm font-medium transition-colors"
            >
              <Sparkles className="w-4 h-4" />
              New Chat
            </button>
          </div>
        </header>

        {/* Disclaimer */}
        <div className="px-4 py-2 bg-amber/10 border-b border-amber/20">
          <div className="flex items-center justify-center gap-2 text-amber text-xs">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
            <span>
              <strong>DISCLAIMER:</strong> This platform provides factual data only and does not constitute financial advice.
            </span>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-4 py-6">
            {/* Welcome State */}
            {messages.length === 0 && (
              <div className="flex flex-col items-center text-center py-12 animate-fade-in-up">
                <div className="w-16 h-16 rounded-2xl bg-emerald flex items-center justify-center mb-6 shadow-lg shadow-emerald/20">
                  <Bot className="w-8 h-8 text-surface-container-lowest" />
                </div>
                <h2 className="text-3xl font-semibold text-on-surface mb-3">
                  How can I assist you today?
                </h2>
                <p className="text-on-surface-variant max-w-md mb-8">
                  Ask me anything about mutual fund regulations, expense ratios, or performance metrics from verified sources.
                </p>

                <div className="w-full bg-surface-container rounded-2xl border border-outline-variant p-6 mb-8">
                  <div className="flex items-center gap-2 mb-4 text-sm text-emerald">
                    <ShieldCheck className="w-4 h-4" />
                    <span className="font-medium">SYSTEM ONLINE</span>
                  </div>
                  <p className="text-on-surface-variant text-sm leading-relaxed">
                    Hello. I am your factual Mutual Fund Assistant. I can help you understand expense ratios, asset allocations, risk metrics, and historical compliance data. How can I assist your research today?
                  </p>
                </div>

                {/* Example Chips */}
                <div className="flex flex-wrap justify-center gap-2 mb-8">
                  {EXAMPLE_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      onClick={() => handleSend(q)}
                      className="px-4 py-2 rounded-xl border border-outline-variant text-sm text-on-surface-variant hover:border-primary hover:text-primary transition-colors bg-surface-container-low"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Messages */}
            <div className="flex flex-col gap-6">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 animate-fade-in-up ${
                    message.role === "user" ? "flex-row-reverse" : ""
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                      message.role === "user"
                        ? "bg-surface-container-high text-on-surface"
                        : "bg-emerald text-surface-container-lowest"
                    }`}
                  >
                    {message.role === "user" ? (
                      <User className="w-4 h-4" />
                    ) : (
                      <Bot className="w-4 h-4" />
                    )}
                  </div>
                  <div
                    className={`max-w-[80%] rounded-2xl px-5 py-4 ${
                      message.role === "user"
                        ? "bg-surface-container-high text-on-surface rounded-br-md"
                        : "bg-surface-container border border-outline-variant text-on-surface rounded-bl-md"
                    }`}
                  >
                    {message.role === "user" ? (
                      <p className="text-sm">{message.content.answer_sentences?.[0]}</p>
                    ) : (
                      <BotMessageContent content={message.content} />
                    )}
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex gap-3 animate-fade-in-up">
                  <div className="w-8 h-8 rounded-xl bg-emerald text-surface-container-lowest flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="bg-surface-container border border-outline-variant rounded-2xl rounded-bl-md px-5 py-4 flex items-center gap-3 text-on-surface-variant">
                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                    <span className="text-sm">Analyzing verified sources...</span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>
        </div>

        {/* Input Area */}
        <div className="px-4 py-4 border-t border-outline-variant bg-surface-container-low">
          <div className="max-w-3xl mx-auto">
            <div className="relative flex items-center gap-2 bg-surface-container rounded-xl border border-outline-variant px-4 py-3 focus-within:border-primary transition-colors">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about fund methodology, ratios, or historical data..."
                className="flex-1 bg-transparent text-sm text-on-surface placeholder-on-surface-variant outline-none"
                disabled={isLoading}
              />
              <button
                onClick={() => handleSend()}
                disabled={isLoading || !input.trim()}
                className="w-9 h-9 rounded-lg bg-emerald hover:bg-emerald/90 disabled:bg-surface-container-high disabled:text-on-surface-variant text-surface-container-lowest flex items-center justify-center transition-colors shrink-0"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <p className="text-center text-xs text-on-surface-variant mt-2">
              Press Enter to send. Shift+Enter for new line.
            </p>
          </div>
        </div>

        {/* Footer */}
        <footer className="px-6 py-3 border-t border-outline-variant bg-surface-container-lowest flex items-center justify-between text-xs text-on-surface-variant">
          <div className="flex items-center gap-1">
            <span className="font-medium text-on-surface">Mutual Fund FAQ Assistant</span>
            <span>2024</span>
          </div>
          <div className="flex items-center gap-4">
            {["Legal Disclaimer", "Privacy Policy", "Data Sources", "Terms of Service"].map(
              (link) => (
                <button key={link} className="hover:text-on-surface transition-colors">
                  {link}
                </button>
              )
            )}
          </div>
        </footer>
      </main>
    </div>
  );
}

function BotMessageContent({ content }: { content: ChatResponse }) {
  if (content.error) {
    return (
      <div className="text-rose bg-rose/10 rounded-lg p-3 text-sm border border-rose/20">
        <strong>Error:</strong> {content.error}
      </div>
    );
  }

  const isRefusal = !content.grounded;

  return (
    <div className="space-y-3">
      {content.answer_sentences?.map((sentence, i) => (
        <p key={i} className="text-sm leading-relaxed">
          {sentence}
        </p>
      ))}

      {content.citation_url && (
        <div className="bg-surface-container-high rounded-lg p-3 text-sm flex items-start gap-2 border border-outline-variant">
          <ShieldCheck className="w-4 h-4 text-emerald shrink-0 mt-0.5" />
          <div>
            <span className="font-medium text-on-surface">Verified Source: </span>
            <a
              href={content.citation_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline break-all inline-flex items-center gap-1"
            >
              {content.citation_url}
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      )}

      {content.footer && (
        <div className="bg-surface-container-low text-on-surface-variant text-xs italic rounded-lg p-3 text-center border border-outline-variant">
          {content.footer}
        </div>
      )}

      {content.educational_links && content.educational_links.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-on-surface">Educational Resources:</p>
          {content.educational_links.map((link, i) => (
            <a
              key={i}
              href={link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary hover:underline break-all flex items-center gap-1"
            >
              <ExternalLink className="w-3 h-3" />
              {link}
            </a>
          ))}
        </div>
      )}

      {isRefusal && !content.educational_links?.length && !content.error && (
        <div className="text-on-surface-variant text-xs mt-2">
          This response is based on policy guidelines.
        </div>
      )}

      {/* Message Actions */}
      {content.grounded && (
        <div className="flex items-center gap-2 pt-2 border-t border-outline-variant">
          <button className="p-1.5 rounded-md text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface transition-colors">
            <Copy className="w-3.5 h-3.5" />
          </button>
          <button className="p-1.5 rounded-md text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface transition-colors">
            <ThumbsUp className="w-3.5 h-3.5" />
          </button>
          <button className="p-1.5 rounded-md text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface transition-colors">
            <ThumbsDown className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
