import React, { useState, useRef } from 'react';

function App() {
  const [resumeFile, setResumeFile] = useState(null);
  const [jdFile, setJdFile] = useState(null);
  const [jdText, setJdText] = useState('');
  const [jdType, setJdType] = useState('text'); // 'text' or 'file'
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [resumeText, setResumeText] = useState(null);
  const [jdExtractedText, setJdExtractedText] = useState(null);
  const [status, setStatus] = useState(null);

  const resumeInputRef = useRef(null);
  const jdInputRef = useRef(null);

  const handleResumeChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        setStatus({ text: "Only PDF files are supported for resumes.", type: "error" });
        return;
      }
      setResumeFile(file);
      setStatus(null);
    }
  };

  const handleJdFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        setStatus({ text: "Only PDF files are supported for job descriptions.", type: "error" });
        return;
      }
      setJdFile(file);
      setStatus(null);
    }
  };

  const triggerResumeUpload = () => resumeInputRef.current.click();
  const triggerJdUpload = () => jdInputRef.current.click();

  const clearResume = () => {
    setResumeFile(null);
    setResumeText(null);
    if (resumeInputRef.current) resumeInputRef.current.value = '';
  };

  const clearJdFile = () => {
    setJdFile(null);
    setJdExtractedText(null);
    if (jdInputRef.current) jdInputRef.current.value = '';
  };

  const handleAnalyze = async () => {
    if (!resumeFile) {
      setStatus({ text: "Please upload a resume first.", type: "error" });
      return;
    }
    if (jdType === 'file' && !jdFile) {
      setStatus({ text: "Please upload a Job Description PDF first.", type: "error" });
      return;
    }
    if (jdType === 'text' && !jdText.trim()) {
      setStatus({ text: "Please paste a Job Description first.", type: "error" });
      return;
    }

    setIsAnalyzing(true);
    setStatus(null);
    setResumeText(null);
    setJdExtractedText(null);

    try {
      // 1. Upload Resume
      const resumeFormData = new FormData();
      resumeFormData.append('file', resumeFile);

      const resumeRes = await fetch('http://localhost:8000/api/upload-resume', {
        method: 'POST',
        body: resumeFormData,
      });

      if (!resumeRes.ok) {
        const err = await resumeRes.json();
        throw new Error(err.detail || 'Failed to process resume');
      }

      const resumeData = await resumeRes.json();
      setResumeText(resumeData.text);

      // 2. Upload JD
      const jdFormData = new FormData();
      if (jdType === 'file') {
        jdFormData.append('file', jdFile);
      } else {
        jdFormData.append('description_text', jdText);
      }

      const jdRes = await fetch('http://localhost:8000/api/upload-jd', {
        method: 'POST',
        body: jdFormData,
      });

      if (!jdRes.ok) {
        const err = await jdRes.json();
        throw new Error(err.detail || 'Failed to process job description');
      }

      const jdData = await jdRes.json();
      setJdExtractedText(jdData.text);

      setStatus({ text: "Resume and Job Description successfully analyzed and extracted!", type: "success" });
    } catch (error) {
      setStatus({ text: error.message, type: "error" });
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <>
      <header className="header">
        <div className="container header-inner">
          <div className="logo">
            <span className="logo-icon">🚀</span>
            AI Career Copilot
          </div>
          <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
            System Architecture Session 1
          </div>
        </div>
      </header>

      <main className="container" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <section className="hero">
          <h1>Analyze Your <span className="highlight">Job Fit</span> Instantly</h1>
          <p>
            Upload your resume and the target job description to extract core competencies, 
            skills, and preview what the parser extracts.
          </p>
        </section>

        <section className="workspace-grid">
          {/* Card 1: Resume Upload */}
          <div className="card">
            <h2 className="card-title">
              <span>📄</span> Resume Upload
            </h2>
            <p style={{ fontSize: '14px', margin: '-10px 0 0' }}>
              Upload your resume in PDF format to parse your skills and experience.
            </p>
            
            <input 
              type="file" 
              ref={resumeInputRef} 
              onChange={handleResumeChange} 
              accept=".pdf" 
              className="file-input"
            />

            {!resumeFile ? (
              <div className="upload-zone" onClick={triggerResumeUpload}>
                <div className="upload-icon">📤</div>
                <div><strong>Click to upload</strong> or drag and drop</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>PDF up to 10MB</div>
              </div>
            ) : (
              <div className="file-info">
                <div className="file-name">
                  <span>📎</span>
                  {resumeFile.name}
                </div>
                <button className="remove-file" onClick={clearResume} title="Remove file">
                  ✕
                </button>
              </div>
            )}
          </div>

          {/* Card 2: JD Upload */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 className="card-title">
                <span>💼</span> Job Description
              </h2>
              <div className="tabs">
                <button 
                  className={`tab-btn ${jdType === 'text' ? 'active' : ''}`}
                  onClick={() => setJdType('text')}
                >
                  Paste Text
                </button>
                <button 
                  className={`tab-btn ${jdType === 'file' ? 'active' : ''}`}
                  onClick={() => setJdType('file')}
                >
                  Upload PDF
                </button>
              </div>
            </div>
            
            <p style={{ fontSize: '14px', margin: '-10px 0 0' }}>
              Provide the role requirements for our agents to perform the gap analysis.
            </p>

            {jdType === 'text' ? (
              <textarea 
                className="text-area"
                placeholder="Paste the job description details here..."
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
              />
            ) : (
              <>
                <input 
                  type="file" 
                  ref={jdInputRef} 
                  onChange={handleJdFileChange} 
                  accept=".pdf" 
                  className="file-input"
                />
                {!jdFile ? (
                  <div className="upload-zone" onClick={triggerJdUpload}>
                    <div className="upload-icon">📥</div>
                    <div><strong>Click to upload JD</strong> or drag and drop</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>PDF up to 10MB</div>
                  </div>
                ) : (
                  <div className="file-info">
                    <div className="file-name">
                      <span>📎</span>
                      {jdFile.name}
                    </div>
                    <button className="remove-file" onClick={clearJdFile} title="Remove file">
                      ✕
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </section>

        {/* Action Button & Status */}
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <button 
            className="btn" 
            onClick={handleAnalyze} 
            disabled={isAnalyzing || !resumeFile || (jdType === 'file' ? !jdFile : !jdText.trim())}
          >
            {isAnalyzing ? (
              <>
                <span className="spinner"></span>
                Extracting Documents...
              </>
            ) : (
              <>
                <span>⚡</span>
                Analyze Fit
              </>
            )}
          </button>

          {status && (
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <div className={`status-msg ${status.type}`}>
                <span>{status.type === 'success' ? '✓' : '⚠'}</span>
                {status.text}
              </div>
            </div>
          )}
        </div>

        {/* Results Panel */}
        {(resumeText || jdExtractedText) && (
          <section className="results-section">
            <h2 style={{ textAlign: 'left', fontSize: '24px' }}>Extracted Text Output</h2>
            <div className="results-grid">
              {/* Resume Text */}
              {resumeText && (
                <div>
                  <div className="panel-header">
                    <span className="panel-title">Extracted Resume</span>
                    <span className="char-count">{resumeText.length} characters</span>
                  </div>
                  <div className="text-viewer">{resumeText}</div>
                </div>
              )}

              {/* JD Text */}
              {jdExtractedText && (
                <div>
                  <div className="panel-header">
                    <span className="panel-title">Extracted Job Description</span>
                    <span className="char-count">{jdExtractedText.length} characters</span>
                  </div>
                  <div className="text-viewer">{jdExtractedText}</div>
                </div>
              )}
            </div>
          </section>
        )}
      </main>

      <footer className="footer">
        <div className="container">
          <p>© {new Date().getFullYear()} AI Career Copilot. Interactive System Design Demo.</p>
        </div>
      </footer>
    </>
  );
}

export default App;
