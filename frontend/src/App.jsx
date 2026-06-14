import React, { useState, useRef, useEffect } from 'react';

function ChatMessageItem({ msg }) {
  const [showSources, setShowSources] = useState(false);
  
  return (
    <div className={`chat-message ${msg.role}`}>
      <div style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
      {msg.sources && msg.sources.length > 0 && (
        <div className="citations-wrapper">
          <button 
            className="citations-toggle" 
            onClick={() => setShowSources(!showSources)}
          >
            🔍 {showSources ? 'Hide Sources' : `View Sources (${msg.sources.length})`}
          </button>
          
          {showSources && (
            <div className="citations-list">
              {msg.sources.map((src, index) => (
                <div key={index} className="citation-card">
                  <div className="citation-card-header">
                    <span>📄 {src.source}</span>
                    <span>Chunk #{src.chunk_index}</span>
                  </div>
                  <div className="citation-card-body">
                    "{src.text}"
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function App() {
  const [activeModule, setActiveModule] = useState('planner'); // 'planner' or 'knowledge'
  
  const [resumeFile, setResumeFile] = useState(null);
  const [jdFile, setJdFile] = useState(null);
  const [jdText, setJdText] = useState('');
  const [jdType, setJdType] = useState('text'); // 'text' or 'file'
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  // Database cached models state
  const [resumeText, setResumeText] = useState(null);
  const [resumeStructured, setResumeStructured] = useState(null);
  const [jdExtractedText, setJdExtractedText] = useState(null);
  const [jdStructured, setJdStructured] = useState(null);
  
  // Gap Analysis & Roadmap state
  const [matchScore, setMatchScore] = useState(null);
  const [missingSkills, setMissingSkills] = useState([]);
  const [recommendations, setRecommendations] = useState(null);
  const [roadmap, setRoadmap] = useState(null);

  const [status, setStatus] = useState(null);
  const [resultsTab, setResultsTab] = useState('analysis'); // 'analysis', 'structured', or 'raw'

  // Knowledge Assistant states
  const [kbFile, setKbFile] = useState(null);
  const [isUploadingKb, setIsUploadingKb] = useState(false);
  const [uploadedKbFiles, setUploadedKbFiles] = useState([]);
  
  const [kbQuery, setKbQuery] = useState('');
  const [isQueryingKb, setIsQueryingKb] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      text: 'Hello! I am your RAG Knowledge Assistant. Upload study notes or technical PDFs on the left, and ask me anything about them here. I will answer with grounded citations from your materials.',
      sources: []
    }
  ]);

  const resumeInputRef = useRef(null);
  const jdInputRef = useRef(null);
  const kbFileInputRef = useRef(null);
  const chatEndRef = useRef(null);


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
    setResumeStructured(null);
    setMatchScore(null);
    setMissingSkills([]);
    setRecommendations(null);
    setRoadmap(null);
    if (resumeInputRef.current) resumeInputRef.current.value = '';
  };

  const clearJdFile = () => {
    setJdFile(null);
    setJdExtractedText(null);
    setJdStructured(null);
    setMatchScore(null);
    setMissingSkills([]);
    setRecommendations(null);
    setRoadmap(null);
    if (jdInputRef.current) jdInputRef.current.value = '';
  };

  const handleKbFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        setStatus({ text: "Only PDF files are supported for study notes.", type: "error" });
        return;
      }
      setKbFile(file);
      setStatus(null);
    }
  };

  const uploadKbFile = async () => {
    if (!kbFile) return;
    setIsUploadingKb(true);
    setStatus(null);
    try {
      const formData = new FormData();
      formData.append('file', kbFile);

      const res = await fetch('http://localhost:8000/api/upload-knowledge', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to index study notes');
      }

      const data = await res.json();
      setUploadedKbFiles((prev) => [
        ...prev,
        { name: data.filename, chunks: data.chunks_ingested }
      ]);
      setKbFile(null);
      if (kbFileInputRef.current) kbFileInputRef.current.value = '';
      setStatus({ text: `Successfully indexed '${data.filename}' into vector database!`, type: "success" });
    } catch (error) {
      setStatus({ text: error.message, type: "error" });
    } finally {
      setIsUploadingKb(false);
    }
  };

  const sendKbQuery = async () => {
    if (!kbQuery.trim() || isQueryingKb) return;
    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: kbQuery.trim(),
      sources: []
    };
    setChatMessages((prev) => [...prev, userMessage]);
    const currentQuery = kbQuery.trim();
    setKbQuery('');
    setIsQueryingKb(true);

    try {
      const res = await fetch('http://localhost:8000/api/query-knowledge', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: currentQuery }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Query request failed');
      }

      const data = await res.json();
      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        text: data.answer,
        sources: data.sources || []
      };
      setChatMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errMessage = {
        id: `err-${Date.now()}`,
        role: 'system',
        text: `Error contacting the knowledge assistant: ${error.message}`,
        sources: []
      };
      setChatMessages((prev) => [...prev, errMessage]);
    } finally {
      setIsQueryingKb(false);
    }
  };

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, isQueryingKb]);

  useEffect(() => {
    const fetchIndexedDocs = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/knowledge-documents');
        if (res.ok) {
          const data = await res.json();
          setUploadedKbFiles(data);
        }
      } catch (error) {
        console.error("Failed to fetch indexed documents:", error);
      }
    };
    fetchIndexedDocs();
  }, []);


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
    setResumeStructured(null);
    setJdExtractedText(null);
    setJdStructured(null);
    setMatchScore(null);
    setMissingSkills([]);
    setRecommendations(null);
    setRoadmap(null);

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
      setResumeStructured(resumeData.structured);

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
      setJdStructured(jdData.structured);

      // 3. Trigger Unified Gap & Roadmap Analysis
      const analyzeRes = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resume_id: resumeData.id,
          jd_id: jdData.id
        })
      });

      if (!analyzeRes.ok) {
        const err = await analyzeRes.json();
        throw new Error(err.detail || 'Failed to analyze fit requirements');
      }

      const analyzeData = await analyzeRes.json();
      setMatchScore(analyzeData.match_score);
      setMissingSkills(analyzeData.missing_skills);
      setRecommendations(analyzeData.recommendations);
      setRoadmap(analyzeData.roadmap);

      // Successfully processed, select analysis tab
      setResultsTab('analysis');
      setStatus({ text: "Competency gap analysis and learning roadmaps calculated successfully!", type: "success" });
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
        <div className="nav-tabs-container">
          <button 
            className={`nav-tab-btn ${activeModule === 'planner' ? 'active' : ''}`}
            onClick={() => {
              setActiveModule('planner');
              setStatus(null);
            }}
          >
            💼 Career Path Planner
          </button>
          <button 
            className={`nav-tab-btn ${activeModule === 'knowledge' ? 'active' : ''}`}
            onClick={() => {
              setActiveModule('knowledge');
              setStatus(null);
            }}
          >
            🧠 Knowledge Assistant
          </button>
        </div>

        {activeModule === 'planner' && (
          <>
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
                    Running Analysis Agents...
                  </>
                ) : (
                  <>
                    <span>⚡</span>
                    Analyze Fit
                  </>
                )}
              </button>

              {status && activeModule === 'planner' && (
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
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <h2 style={{ fontSize: '24px' }}>Analysis Output</h2>
                  <div className="tabs">
                    <button 
                      className={`tab-btn ${resultsTab === 'analysis' ? 'active' : ''}`}
                      onClick={() => setResultsTab('analysis')}
                    >
                      Fit & Roadmap
                    </button>
                    <button 
                      className={`tab-btn ${resultsTab === 'structured' ? 'active' : ''}`}
                      onClick={() => setResultsTab('structured')}
                    >
                      Structured Entities
                    </button>
                    <button 
                      className={`tab-btn ${resultsTab === 'raw' ? 'active' : ''}`}
                      onClick={() => setResultsTab('raw')}
                    >
                      Raw Text Preview
                    </button>
                  </div>
                </div>

                {resultsTab === 'raw' && (
                  <div className="results-grid">
                    {/* Resume Raw Text */}
                    {resumeText && (
                      <div>
                        <div className="panel-header">
                          <span className="panel-title">Extracted Resume Raw</span>
                          <span className="char-count">{resumeText.length} characters</span>
                        </div>
                        <div className="text-viewer">{resumeText}</div>
                      </div>
                    )}

                    {/* JD Raw Text */}
                    {jdExtractedText && (
                      <div>
                        <div className="panel-header">
                          <span className="panel-title">Extracted JD Raw</span>
                          <span className="char-count">{jdExtractedText.length} characters</span>
                        </div>
                        <div className="text-viewer">{jdExtractedText}</div>
                      </div>
                    )}
                  </div>
                )}

                {resultsTab === 'structured' && (
                  <div className="results-grid">
                    {/* Resume Structured Parse */}
                    <div>
                      <div className="panel-header">
                        <span className="panel-title">Resume Structured Extractor</span>
                        <span className="char-count">Parsed by AI Resume Agent</span>
                      </div>
                      <div className="structured-viewer">
                        {resumeStructured ? (
                          <>
                            <div className="entity-section">
                              <div className="entity-section-title">Skills parsed</div>
                              <div className="tag-cloud">
                                {resumeStructured.skills?.map((skill, index) => (
                                  <span key={index} className="tag">{skill}</span>
                                ))}
                              </div>
                            </div>

                            <div className="entity-section">
                              <div className="entity-section-title">Work Experience</div>
                              {resumeStructured.experience?.map((exp, index) => (
                                <div key={index} className="experience-card">
                                  <div className="card-header-flex">
                                    <span className="card-h3">{exp.role}</span>
                                    <span className="card-meta">{exp.duration}</span>
                                  </div>
                                  <div className="card-sub">{exp.company}</div>
                                  <ul className="bullet-list">
                                    {exp.highlights?.map((hl, idx) => (
                                      <li key={idx}>{hl}</li>
                                    ))}
                                  </ul>
                                </div>
                              ))}
                            </div>

                            <div className="entity-section">
                              <div className="entity-section-title">Projects</div>
                              {resumeStructured.projects?.map((proj, index) => (
                                <div key={index} className="project-card">
                                  <div className="card-header-flex">
                                    <span className="card-h3">{proj.title}</span>
                                  </div>
                                  <div className="tag-cloud" style={{ margin: '4px 0 8px' }}>
                                    {proj.tech_stack?.map((tech, idx) => (
                                      <span key={idx} className="tag tag-secondary" style={{ fontSize: '10px', padding: '2px 6px' }}>
                                        {tech}
                                      </span>
                                    ))}
                                  </div>
                                  <p style={{ fontSize: '13px', margin: 0 }}>{proj.description}</p>
                                </div>
                              ))}
                            </div>

                            <div className="entity-section">
                              <div className="entity-section-title">Education</div>
                              {resumeStructured.education?.map((edu, index) => (
                                <div key={index} className="experience-card" style={{ padding: '12px 16px' }}>
                                  <div className="card-header-flex">
                                    <span className="card-h3">{edu.degree} in {edu.major}</span>
                                  </div>
                                  <div className="card-sub" style={{ fontSize: '12.5px' }}>{edu.institution}</div>
                                </div>
                              ))}
                            </div>
                          </>
                        ) : (
                          <p style={{ color: 'var(--text-muted)' }}>No structured data loaded.</p>
                        )}
                      </div>
                    </div>

                    {/* JD Structured Parse */}
                    <div>
                      <div className="panel-header">
                        <span className="panel-title">JD Structured Extractor</span>
                        <span className="char-count">Parsed by AI JD Agent</span>
                      </div>
                      <div className="structured-viewer">
                        {jdStructured ? (
                          <>
                            <div className="entity-section">
                              <div className="entity-section-title">Role Profile</div>
                              <div className="experience-card">
                                <div className="card-header-flex">
                                  <span className="card-h3" style={{ fontSize: '16px' }}>{jdStructured.job_title}</span>
                                </div>
                                <div className="card-sub" style={{ marginBottom: '8px' }}>
                                  {jdStructured.company || 'Not Specified'}
                                </div>
                                <div className="card-meta">
                                  Experience Requirement: <strong>{jdStructured.experience_required || 'Not Specified'}</strong>
                                </div>
                              </div>
                            </div>

                            <div className="entity-section">
                              <div className="entity-section-title">Required Skills</div>
                              <div className="tag-cloud">
                                {jdStructured.required_skills?.map((skill, index) => (
                                  <span key={index} className="tag">{skill}</span>
                                ))}
                              </div>
                            </div>

                            <div className="entity-section">
                              <div className="entity-section-title">Preferred Skills</div>
                              <div className="tag-cloud">
                                {jdStructured.preferred_skills?.map((skill, index) => (
                                  <span key={index} className="tag tag-secondary">{skill}</span>
                                ))}
                              </div>
                            </div>
                          </>
                        ) : (
                          <p style={{ color: 'var(--text-muted)' }}>No structured data loaded.</p>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {resultsTab === 'analysis' && (
                  <div className="results-grid">
                    {/* Left Column: Match score details */}
                    <div>
                      <div className="panel-header">
                        <span className="panel-title">Hiring Fit Evaluation</span>
                        <span className="char-count">Computed by Gap Agent</span>
                      </div>
                      <div className="score-card-flex" style={{ background: 'rgba(18, 14, 28, 0.8)', border: '1px solid var(--card-border)', height: '480px', overflowY: 'auto', display: 'block', textAlign: 'left' }}>
                        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '24px' }}>
                          <div className={`score-dial ${matchScore >= 80 ? 'score-good' : matchScore >= 50 ? 'score-average' : 'score-poor'}`}>
                            <span className="score-text">{matchScore !== null ? `${matchScore}%` : '--'}</span>
                            <span className="score-label">Fit Score</span>
                          </div>
                        </div>

                        <div className="entity-section">
                          <div className="entity-section-title">Missing Skill Gaps</div>
                          {missingSkills.length > 0 ? (
                            <div className="tag-cloud">
                              {missingSkills.map((skill, index) => (
                                <span key={index} className="tag tag-warning">{skill}</span>
                              ))}
                            </div>
                          ) : (
                            <p style={{ color: 'var(--success)', fontWeight: '500', fontSize: '13.5px', margin: 0 }}>
                              ✓ Perfect match! You demonstrate all required and preferred skills.
                            </p>
                          )}
                        </div>

                        {recommendations && (
                          <div className="entity-section" style={{ margin: 0 }}>
                            <div className="entity-section-title">Mentor Recommendations</div>
                            <p style={{ fontSize: '13px', whiteSpace: 'pre-line', margin: 0, color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                              {recommendations}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Right Column: Dynamic Roadmap */}
                    <div>
                      <div className="panel-header">
                        <span className="panel-title">Actionable Syllabus</span>
                        <span className="char-count">Roadmap Agent Timeline</span>
                      </div>
                      <div className="structured-viewer">
                        {roadmap && roadmap.weeks && roadmap.weeks.length > 0 ? (
                          <div className="timeline">
                            {roadmap.weeks.map((wk, index) => (
                              <div key={index} className="timeline-week">
                                <div className="timeline-header">
                                  Week {wk.week_number}: {wk.theme}
                                </div>
                                <div className="tag-cloud" style={{ margin: '4px 0 12px' }}>
                                  {wk.focus_skills?.map((skill, idx) => (
                                    <span key={idx} className="tag tag-secondary" style={{ fontSize: '10px', padding: '2px 8px' }}>
                                      {skill}
                                    </span>
                                  ))}
                                </div>
                                
                                <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)', marginTop: '8px' }}>Study Checklist:</div>
                                <ul className="task-list">
                                  {wk.tasks?.map((task, idx) => (
                                    <li key={idx}>{task}</li>
                                  ))}
                                </ul>

                                <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)', marginTop: '8px' }}>References & Reading:</div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '6px' }}>
                                  {wk.resources?.map((res, idx) => {
                                    let label = res;
                                    let url = "#";
                                    if (res.includes("http")) {
                                      const idxUrl = res.indexOf("http");
                                      label = res.substring(0, idxUrl).replace(/[\(:\-]/g, '').trim();
                                      url = res.substring(idxUrl).replace(/\)/g, '').trim();
                                    }
                                    return (
                                      <a key={idx} href={url} target="_blank" rel="noopener noreferrer" className="resource-link">
                                        📖 {label || "Official Documentation Link"}
                                      </a>
                                    );
                                  })}
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p style={{ color: 'var(--text-muted)', fontSize: '13.5px' }}>
                            No weekly timelines necessary. You already meet the target job description criteria!
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </section>
            )}
          </>
        )}

        {activeModule === 'knowledge' && (
          <>
            <section className="hero">
              <h1>Interact With Your <span className="highlight">Study Material</span></h1>
              <p>
                Upload your technical lecture notes, textbooks, or reference sheets and ask questions.
                Your answers are strictly grounded in your materials.
              </p>
            </section>

            <div className="knowledge-grid">
              {/* Left Column: Upload study notes */}
              <div className="card">
                <h2 className="card-title">
                  <span>📚</span> Study Resources
                </h2>
                <p style={{ fontSize: '14px', margin: '-10px 0 0' }}>
                  Index textbook excerpts, lecture slides, or cheat sheets in ChromaDB.
                </p>
                
                <input 
                  type="file" 
                  ref={kbFileInputRef} 
                  onChange={handleKbFileChange} 
                  accept=".pdf" 
                  className="file-input"
                />

                {!kbFile ? (
                  <div className="upload-zone" onClick={() => kbFileInputRef.current.click()}>
                    <div className="upload-icon">📤</div>
                    <div><strong>Click to upload Notes PDF</strong> or drag and drop</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>PDF up to 10MB</div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div className="file-info">
                      <div className="file-name">
                        <span>📎</span>
                        {kbFile.name}
                      </div>
                      <button className="remove-file" onClick={() => setKbFile(null)} title="Clear selection">
                        ✕
                      </button>
                    </div>
                    <button 
                      className="btn" 
                      onClick={uploadKbFile}
                      disabled={isUploadingKb}
                      style={{ width: '100%' }}
                    >
                      {isUploadingKb ? (
                        <>
                          <span className="spinner"></span>
                          Extracting & Embedding...
                        </>
                      ) : (
                        <>
                          <span>⚡</span>
                          Index Document
                        </>
                      )}
                    </button>
                  </div>
                )}

                {status && activeModule === 'knowledge' && (
                  <div className={`status-msg ${status.type}`} style={{ marginTop: '0px' }}>
                    <span>{status.type === 'success' ? '✓' : '⚠'}</span>
                    {status.text}
                  </div>
                )}

                <div style={{ marginTop: '16px' }}>
                  <h3 style={{ fontSize: '14px', textTransform: 'uppercase', color: 'var(--accent-secondary)', marginBottom: '12px' }}>
                    Indexed Knowledge Documents ({uploadedKbFiles.length})
                  </h3>
                  <div className="doc-list">
                    {uploadedKbFiles.length === 0 ? (
                      <div style={{ fontSize: '13.5px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                        No notes uploaded yet. Add a PDF to query against it.
                      </div>
                    ) : (
                      uploadedKbFiles.map((file, idx) => (
                        <div key={idx} className="doc-item">
                          <div className="doc-item-info">
                            <span>📄</span>
                            <span title={file.name} style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {file.name}
                            </span>
                          </div>
                          <span className="doc-item-badge">{file.chunks} chunks</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>

              {/* Right Column: Grounded AI Assistant Chat */}
              <div className="card chat-card">
                <div className="chat-header">
                  <h2 className="card-title" style={{ fontSize: '18px' }}>
                    <span>💬</span> Grounded AI Assistant
                  </h2>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    {isQueryingKb ? 'Searching knowledge database...' : 'RAG Pipeline Active'}
                  </span>
                </div>

                <div className="chat-messages">
                  {chatMessages.map((msg) => (
                    <ChatMessageItem key={msg.id} msg={msg} />
                  ))}
                  {isQueryingKb && (
                    <div className="chat-message assistant" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span className="spinner" style={{ width: '14px', height: '14px', borderWidth: '1.5px' }}></span>
                      Fetching candidate contexts & synthesizing response...
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>

                <div className="chat-input-area">
                  <input 
                    type="text" 
                    className="chat-input"
                    placeholder="Ask a question about your study materials..."
                    value={kbQuery}
                    onChange={(e) => setKbQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') sendKbQuery();
                    }}
                    disabled={isQueryingKb}
                  />
                  <button 
                    className="chat-send-btn"
                    onClick={sendKbQuery}
                    disabled={isQueryingKb || !kbQuery.trim()}
                  >
                    ➔
                  </button>
                </div>
              </div>
            </div>
          </>
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
