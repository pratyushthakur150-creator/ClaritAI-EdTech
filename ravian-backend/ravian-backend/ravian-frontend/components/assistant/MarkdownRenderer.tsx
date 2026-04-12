'use client'

import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

interface MarkdownRendererProps {
  content: string
}

/**
 * Pre-process the raw LLM response so remark-math can detect the formulas:
 *  • \( ... \)  →  $ ... $      (inline math)
 *  • \[ ... \]  →  $$ ... $$    (block math)
 *  • \boxed{X}  →  \boxed{X}    (already KaTeX-compatible)
 */
function preprocessLatex(text: string): string {
  // Block math  \[ ... \]  →  $$ ... $$
  let result = text.replace(/\\\[([\s\S]*?)\\\]/g, (_, inner) => `$$${inner}$$`)
  // Inline math  \( ... \)  →  $ ... $
  result = result.replace(/\\\(([\s\S]*?)\\\)/g, (_, inner) => `$${inner}$`)
  return result
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const processed = preprocessLatex(content)

  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          // Headings
          h1: ({ children }) => (
            <h1 className="text-xl font-bold mt-4 mb-2 text-gray-900">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-bold mt-3 mb-2 text-gray-900">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-semibold mt-3 mb-1 text-gray-800">{children}</h3>
          ),
          // Paragraphs
          p: ({ children }) => (
            <p className="mb-2 leading-relaxed">{children}</p>
          ),
          // Strong / Bold
          strong: ({ children }) => (
            <strong className="font-semibold text-gray-900">{children}</strong>
          ),
          // Lists
          ul: ({ children }) => (
            <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="leading-relaxed">{children}</li>
          ),
          // Code blocks
          code: ({ className, children, ...props }) => {
            const isBlock = className?.includes('language-')
            if (isBlock) {
              return (
                <pre className="bg-gray-800 text-gray-100 rounded-lg p-3 my-2 overflow-x-auto text-sm">
                  <code className={className} {...props}>{children}</code>
                </pre>
              )
            }
            return (
              <code className="bg-indigo-50 text-indigo-700 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                {children}
              </code>
            )
          },
          // Blockquote
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-indigo-300 pl-3 my-2 text-gray-700 italic">
              {children}
            </blockquote>
          ),
          // Horizontal rule
          hr: () => <hr className="my-3 border-gray-200" />,
          // Table
          table: ({ children }) => (
            <div className="overflow-x-auto my-2">
              <table className="min-w-full text-sm border border-gray-200 rounded">{children}</table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-gray-50">{children}</thead>
          ),
          th: ({ children }) => (
            <th className="px-3 py-1.5 text-left font-semibold border-b border-gray-200">{children}</th>
          ),
          td: ({ children }) => (
            <td className="px-3 py-1.5 border-b border-gray-100">{children}</td>
          ),
        }}
      >
        {processed}
      </ReactMarkdown>
    </div>
  )
}
