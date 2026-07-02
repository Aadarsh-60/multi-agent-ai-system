import { useState, useRef } from 'react';

function formatContent(text) {
  const lines = String(text || '').split(/\r?\n/);
  const blocks = [];
  let paragraphBuffer = [];
  let codeBuffer = [];
  let inCodeBlock = false;

  const flushParagraph = () => {
    const paragraph = paragraphBuffer.join(' ').trim();
    if (paragraph) {
      blocks.push({ type: 'paragraph', text: paragraph });
    }
    paragraphBuffer = [];
  };

  const flushCodeBlock = () => {
    const code = codeBuffer.join('\n').trim();
    if (code) {
      blocks.push({ type: 'code', text: code });
    }
    codeBuffer = [];
  };

  lines.forEach((rawLine) => {
    const line = rawLine.trim();
    if (!line) {
      flushParagraph();
      return;
    }

    if (/^```/.test(line)) {
      flushParagraph();
      if (inCodeBlock) {
        flushCodeBlock();
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      return;
    }

    if (inCodeBlock) {
      codeBuffer.push(rawLine);
      return;
    }

    if (/^#{1,3}\s+/.test(line)) {
      flushParagraph();
      blocks.push({ type: 'heading', text: line.replace(/^#{1,3}\s+/, '') });
      return;
    }

    if (/^[-*•]\s+/.test(line)) {
      flushParagraph();
      blocks.push({ type: 'bullet', text: line.replace(/^[-*•]\s+/, '') });
      return;
    }

    if (/^\d+\.\s+/.test(line)) {
      flushParagraph();
      blocks.push({ type: 'numbered', text: line.replace(/^\d+\.\s+/, '') });
      return;
    }

    if (/^(important|note|summary|key point|takeaway|action item|next step|overall verdict|issues|improvements|implementation|review notes|next steps):/i.test(line)) {
      flushParagraph();
      blocks.push({ type: 'highlight', text: line });
      return;
    }

    paragraphBuffer.push(line);
  });

  flushParagraph();
  if (inCodeBlock) {
    flushCodeBlock();
  }
  return blocks;
}

function renderInlineText(text) {
  const parts = String(text).split(/(\b(?:important|key|must|critical|recommended|next step|summary|takeaway|overall verdict|issues|improvements|implementation|review notes|next steps)\b)/gi);
  return parts.map((part, index) => {
    const isKeyword = /^(important|key|must|critical|recommended|next step|summary|takeaway|overall verdict|issues|improvements|implementation|review notes|next steps)$/i.test(part);
    return isKeyword ? <strong key={`${part}-${index}`}>{part}</strong> : <span key={`${part}-${index}`}>{part}</span>;
  });
}

function renderCodeBlock(text) {
  const lines = String(text || '').split(/\r?\n/);
  return (
    <div className="code-block">
      {lines.map((line, index) => {
        const trimmed = line.trim();
        if (/^\s*#/.test(trimmed)) {
          return <div className="code-comment" key={`code-${index}`}>{line}</div>;
        }
        if (/^\s*(def|class|return|if|else|for|while|try|except|import|from|with|async|await|lambda)\b/.test(trimmed)) {
          return <div className="code-keyword" key={`code-${index}`}>{line}</div>;
        }
        return <div className="code-line" key={`code-${index}`}>{line}</div>;
      })}
    </div>
  );
}

function renderContent(text, placeholder = 'Waiting for the agents to produce something beautiful.') {
  const blocks = formatContent(text);

  if (!blocks.length) {
    return <div className="empty-state">{placeholder}</div>;
  }

  return (
    <div className="rich-output">
      {blocks.map((block, index) => {
        if (block.type === 'heading') {
          return (
            <h4 className="content-heading" key={`heading-${index}`}>
              {renderInlineText(block.text)}
            </h4>
          );
        }

        if (block.type === 'bullet' || block.type === 'numbered') {
          return (
            <div className="content-bullet" key={`bullet-${index}`}>
              • {renderInlineText(block.text)}
            </div>
          );
        }

        if (block.type === 'highlight') {
          return (
            <div className="highlight-callout" key={`highlight-${index}`}>
              {renderInlineText(block.text)}
            </div>
          );
        }

        if (block.type === 'code') {
          return <div key={`code-${index}`}>{renderCodeBlock(block.text)}</div>;
        }

        return (
          <p className="content-paragraph" key={`paragraph-${index}`}>
            {renderInlineText(block.text)}
          </p>
        );
      })}
    </div>
  );
}

export default function App() {
  const [task, setTask] = useState('');
  const [plan, setPlan] = useState('');
  const [feedback, setFeedback] = useState('');
  const [imageName, setImageName] = useState('');
  const [imageData, setImageData] = useState('');
  const fileInputRef = useRef(null);
  const [research, setResearch] = useState('');
  const [code, setCode] = useState('');
  const [review, setReview] = useState('');
  const [report, setReport] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('Ready');
  const [approved, setApproved] = useState(false);
  const [showApproval, setShowApproval] = useState(false);
  const [modalFeedback, setModalFeedback] = useState('');
  const [activeStream, setActiveStream] = useState('');
  const [streaming, setStreaming] = useState(false);

  function formatErrorMessage(message) {
    const text = String(message || 'Unknown error');
    const normalized = text.toLowerCase();
    if (normalized.includes('resource_exhausted') || normalized.includes('quota') || normalized.includes('429')) {
      return 'Gemini API quota exhausted. Please wait a moment or add billing/credits, then try again.';
    }
    return text.split('\n')[0];
  }

  function handleImageChange(event) {
    const file = event.target.files?.[0];
    if (!file) {
      setImageName('');
      setImageData('');
      return;
    }

    setImageName(file.name);
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result || '';
      if (typeof result === 'string') {
        setImageData(result.split(',')[1] || '');
      }
    };
    reader.readAsDataURL(file);
  }

  function openFilePicker() {
    if (fileInputRef.current) fileInputRef.current.click();
  }

  function streamText(text, setter, onComplete, speed = 16) {
    const content = String(text || '');
    if (!content) {
      setter('');
      onComplete?.();
      return;
    }

    let index = 0;
    setter('');
    const interval = window.setInterval(() => {
      index += 1;
      setter(content.slice(0, index));
      if (index >= content.length) {
        window.clearInterval(interval);
        onComplete?.();
      }
    }, speed);
  }

  async function handlePlan(sendFeedback = '') {
    setLoading(true);
    setStatus('Planning...');
    setShowApproval(false);
    setApproved(false);
    setResearch('');
    setCode('');
    setReview('');
    setReport('');

    try {
      const res = await fetch('/api/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ task, feedback: sendFeedback || feedback, image_name: imageName }),
      });
      const data = await res.json();
      setLoading(false);

      if (data.error) {
        setStatus(`Error: ${formatErrorMessage(data.error)}`);
        setPlan('');
        setShowApproval(false);
        return;
      }

      setPlan(data.plan || '');
      setStatus('Plan ready — review and approve');
      setShowApproval(true);
    } catch (e) {
      setLoading(false);
      setStatus(`Error: ${formatErrorMessage(e.message || e)}`);
    }
  }

  async function handleRun(force = false) {
    if (!force && !approved) {
      setStatus('Approval required');
      setShowApproval(true);
      return;
    }

    setLoading(true);
    setStreaming(true);
    setActiveStream('research');
    setStatus('Research agent is drafting...');
    setResearch('');
    setCode('');
    setReview('');
    setReport('');

    try {
      const res = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task, plan, image_name: imageName, image_data: imageData }),
      });
      const data = await res.json();

      if (data.error) {
        setLoading(false);
        setStreaming(false);
        setStatus(`Error: ${formatErrorMessage(data.error)}`);
        return;
      }

      streamText(data.research_notes || '', setResearch, () => {
        setActiveStream('code');
        setStatus('Coding agent is drafting...');
        streamText(data.code || '', setCode, () => {
          setActiveStream('review');
          setStatus('Review agent is evaluating...');
          streamText(data.review_feedback || '', setReview, () => {
            setActiveStream('report');
            setStatus('Report agent is formatting...');
            streamText(data.final_report || '', setReport, () => {
              setActiveStream('done');
              setLoading(false);
              setStreaming(false);
              setStatus('Completed — the agents have shared their results');
            });
          });
        });
      });
    } catch (e) {
      setLoading(false);
      setStreaming(false);
      setStatus(`Error: ${e.message || e}`);
    }
  }

  async function handleApprove() {
    setApproved(true);
    setShowApproval(false);
    setStatus('Plan approved. Running agents...');
    await handleRun(true);
  }

  async function handleReject() {
    const toSend = modalFeedback || feedback;
    setShowApproval(false);
    setStatus('Revising plan...');
    await handlePlan(toSend);
  }

  function downloadReport() {
    if (!report) return;
    const blob = new Blob([report], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'final_report.txt';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  async function downloadPdf() {
    if (!report) return;
    setLoading(true);
    setStatus('Generating PDF...');
    try {
      const res = await fetch('/api/report_pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report }),
      });
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || 'PDF generation failed');
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'final_report.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setStatus('PDF ready');
    } catch (e) {
      setStatus(`Error: ${formatErrorMessage(e.message || e)}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-root">
      <header className="app-header">
        <h1>🤖 Multi-Agent AI System</h1>
        <p className="muted">Turn a task into a clear plan, get human approval, and let every specialist agent respond in a polished way.</p>
        <div className="status">Status: {status}</div>
      </header>

      <main className="app-main">
        <section className="card hero-card">
          <div className="task-input-container">
            <textarea
              value={task}
              onChange={(e) => setTask(e.target.value)}
              rows={4}
              placeholder="Describe your task"
              className="task-input"
            />

            <input ref={fileInputRef} onChange={handleImageChange} type="file" accept="image/*" style={{ display: 'none' }} />
            <button type="button" className="attach-btn inside" onClick={openFilePicker}>+</button>
            <div className="attach-label inside">Attach image</div>
          </div>
          {imageName ? <div className="file-name">{imageName}</div> : null}

          <div className="controls">
            <button onClick={() => handlePlan()} disabled={loading || !task}>Generate Plan</button>
            <button className="secondary" onClick={() => handleRun()} disabled={loading || !plan}>Run Workflow</button>
            <button className="secondary" onClick={downloadReport} disabled={!report}>Download Report</button>
            <button className="secondary" onClick={downloadPdf} disabled={!report}>Download PDF</button>
          </div>

          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            rows={2}
            placeholder="Optional feedback for the planner"
            className="feedback-input"
          />
        </section>

        {plan ? (
          <section className="card plan-card">
            <div className="card-header">
              <h2>Execution Blueprint</h2>
              <span className="pill">Needs approval</span>
            </div>
            {renderContent(plan, 'The plan will appear here once the planner finishes.')}
          </section>
        ) : null}

        {(approved || research || code || review || report || streaming) && (
          <>
            <section className="card output-card">
              <div className="card-header">
                <h2>Research Notes</h2>
                <span className={`pill ${activeStream === 'research' ? 'active' : 'muted-pill'}`}>Agent: Research</span>
              </div>
              {renderContent(research, 'Research insights will be presented here after execution.')}
            </section>

            <section className="card output-card">
              <div className="card-header">
                <h2>Generated Code</h2>
                <span className={`pill ${activeStream === 'code' ? 'active' : 'muted-pill'}`}>Agent: Coding</span>
              </div>
              {renderContent(code, 'The coding agent will share its implementation here.')}
            </section>

            <section className="card output-card">
              <div className="card-header">
                <h2>Review Feedback</h2>
                <span className={`pill ${activeStream === 'review' ? 'active' : 'muted-pill'}`}>Agent: Review</span>
              </div>
              {renderContent(review, 'Review feedback will appear here once the workflow completes.')}
            </section>

            <section className="card output-card">
              <div className="card-header">
                <h2>Final Report</h2>
                <span className={`pill ${activeStream === 'report' ? 'active' : 'muted-pill'}`}>Agent: Report</span>
              </div>
              {renderContent(report, 'The final report will be assembled here.')}
            </section>
          </>
        )}
      </main>

      {showApproval && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Review the plan before execution</h3>
            <p className="modal-copy">Approve this blueprint to let the research, coding, review, and reporting agents work from it.</p>
            <div className="modal-plan">
              {renderContent(plan, 'The plan will appear here once the planner finishes.')}
            </div>
            <textarea
              rows={3}
              placeholder="Optional feedback to revise the plan"
              value={modalFeedback}
              onChange={(e) => setModalFeedback(e.target.value)}
            />
            <div className="modal-actions">
              <button onClick={handleApprove}>✅ Approve & Run</button>
              <button className="secondary" onClick={handleReject}>❌ Reject & Revise</button>
              <button className="secondary" onClick={() => setShowApproval(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

