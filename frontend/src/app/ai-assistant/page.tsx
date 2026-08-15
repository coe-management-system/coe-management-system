'use client';

import React, { useState } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Bot, Send, User, Info, Sparkles } from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
}

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: '1',
    sender: 'assistant',
    text: 'Hello! I am your AI Academic Operations & CoE Decision Support Assistant. How can I help you analyze attendance shortages, optimize timetable schedules, or verify industry readiness credentials today?',
    timestamp: '10:00 AM',
  },
];

export default function AiAssistantPage() {
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [inputValue, setInputValue] = useState('');
  const [thinking, setThinking] = useState(false);

  const handleSendMessage = (textToSend?: string) => {
    const text = (textToSend || inputValue).trim();
    if (!text) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputValue('');
    setThinking(true);

    setTimeout(() => {
      let replyText = 'Analysis complete. Based on current institutional telemetry, 3 students in Computer Science are flagged for attendance shortages (<75%). Recommend scheduling academic intervention.';
      if (text.toLowerCase().includes('workload') || text.toLowerCase().includes('faculty')) {
        replyText = 'Faculty Workload Audit: Dr. V. Gupta is currently overallocated (24 hrs / wk). Recommend reallocating CS305 lab supervision to Assistant Professor P. Sharma.';
      } else if (text.toLowerCase().includes('certification') || text.toLowerCase().includes('coe')) {
        replyText = 'CoE Certification Summary: NVIDIA Deep Learning Institute track has 45 active enrolled students with an average progress of 78%. 100% verified credential compliance.';
      }

      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: replyText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setThinking(false);
    }, 1000);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI Operational & Decision Support Assistant"
        subtitle="Conversational Intelligence for Resource Allocation, Deficiency Audits & Strategic Recommendations"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'AI Assistant' }]}
      />

      {/* Backend Dependency Banner */}
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-start space-x-3 text-xs text-amber-800">
        <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">Backend Dependency Notice: </span>
          The live AI Assistant API (<code className="bg-amber-100 px-1 py-0.5 rounded text-[11px]">POST /api/v1/ai/query</code>) is pending backend implementation. Client-side query assistant active.
        </div>
      </div>

      {/* Quick Prompt Pills */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-bold text-slate-500 flex items-center space-x-1 mr-1">
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          <span>Quick Prompts:</span>
        </span>
        <button
          onClick={() => handleSendMessage('Summarize Computer Science attendance deficiencies')}
          className="px-3 py-1.5 bg-white hover:bg-indigo-50 border border-slate-200 hover:border-indigo-200 text-slate-700 hover:text-indigo-700 rounded-xl text-xs font-semibold transition-colors shadow-2xs cursor-pointer"
        >
          Attendance Deficiencies
        </button>
        <button
          onClick={() => handleSendMessage('Check faculty workload overallocation status')}
          className="px-3 py-1.5 bg-white hover:bg-indigo-50 border border-slate-200 hover:border-indigo-200 text-slate-700 hover:text-indigo-700 rounded-xl text-xs font-semibold transition-colors shadow-2xs cursor-pointer"
        >
          Faculty Workload Audit
        </button>
        <button
          onClick={() => handleSendMessage('What is the certification progress for NVIDIA CoE?')}
          className="px-3 py-1.5 bg-white hover:bg-indigo-50 border border-slate-200 hover:border-indigo-200 text-slate-700 hover:text-indigo-700 rounded-xl text-xs font-semibold transition-colors shadow-2xs cursor-pointer"
        >
          CoE Certifications
        </button>
      </div>

      {/* Chat Window Container */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xs flex flex-col h-[520px] overflow-hidden">
        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start space-x-3 ${msg.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold shrink-0 ${
                  msg.sender === 'user'
                    ? 'bg-slate-900 text-white'
                    : 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                }`}
              >
                {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div
                className={`max-w-xl p-4 rounded-2xl text-xs leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-indigo-600 text-white rounded-tr-none font-medium'
                    : 'bg-slate-100 text-slate-800 rounded-tl-none font-normal'
                }`}
              >
                <div>{msg.text}</div>
                <div
                  className={`text-[9px] mt-1.5 text-right font-mono ${
                    msg.sender === 'user' ? 'text-indigo-200' : 'text-slate-400'
                  }`}
                >
                  {msg.timestamp}
                </div>
              </div>
            </div>
          ))}

          {thinking && (
            <div className="flex items-center space-x-3 text-xs text-slate-400">
              <div className="w-8 h-8 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
                <Bot className="w-4 h-4 animate-bounce" />
              </div>
              <span className="italic">AI Assistant is processing query telemetry...</span>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/50">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center space-x-2"
          >
            <input
              type="text"
              placeholder="Ask AI Assistant about attendance, workloads, certifications, or room schedules..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="flex-1 px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-600 font-medium"
            />
            <button
              type="submit"
              disabled={!inputValue.trim()}
              className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-sm transition-colors flex items-center space-x-1.5 disabled:opacity-50 cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Ask AI</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
