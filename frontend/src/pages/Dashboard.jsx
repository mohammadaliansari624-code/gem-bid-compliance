import React, { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../api/client'

export default function Dashboard() {
  const { user, logout } = useAuth()
  const [tenders, setTenders] = useState([])
  const [title, setTitle] = useState('')
  const [tenderNumber, setTenderNumber] = useState('')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [extractingId, setExtractingId] = useState(null)
  const [verifyingId, setVerifyingId] = useState(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // View Panels: 'rules' | 'vendor' | 'compliance'
  const [activePanel, setActivePanel] = useState(null)
  const [selectedTender, setSelectedTender] = useState(null)

  // Requirements State
  const [requirements, setRequirements] = useState([])
  const [loadingReqs, setLoadingReqs] = useState(false)

  // Vendor Docs State
  const [vendorDocs, setVendorDocs] = useState([])
  const [docType, setDocType] = useState('GST Certificate')
  const [vendorFile, setVendorFile] = useState(null)
  const [uploadingVendorDoc, setUploadingVendorDoc] = useState(false)

  // Compliance Results State
  const [complianceResults, setComplianceResults] = useState([])
  const [loadingCompliance, setLoadingCompliance] = useState(false)

  const fetchTenders = async () => {
    try {
      const res = await api.get('/tenders/')
      setTenders(res.data)
    } catch (err) {
      console.error('Failed to load tenders:', err)
    }
  }

  useEffect(() => {
    fetchTenders()
  }, [])

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0]
      if (!selected.name.toLowerCase().endsWith('.pdf')) {
        setError('Please select a valid .pdf document.')
        setFile(null)
        return
      }
      setError('')
      setFile(selected)
    }
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!title || !file) {
      setError('Both Tender Title and PDF document are required.')
      return
    }

    const formData = new FormData()
    formData.append('title', title)
    if (tenderNumber) formData.append('tender_number', tenderNumber)
    if (description) formData.append('description', description)
    formData.append('file', file)

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      await api.post('/tenders/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setSuccess('Tender PDF document uploaded successfully.')
      setTitle('')
      setTenderNumber('')
      setDescription('')
      setFile(null)
      e.target.reset()
      fetchTenders()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload tender document.')
    } finally {
      setLoading(false)
    }
  }

  // 1. Extract Requirements
  const handleExtract = async (tender) => {
    setExtractingId(tender.id)
    setError('')
    setSuccess('')
    try {
      const res = await api.post(`/tenders/${tender.id}/extract`)
      setSuccess(`Successfully extracted ${res.data.length} compliance requirement(s) from Tender #${tender.id}.`)
      fetchTenders()
      handleViewRequirements(tender)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to extract requirements.')
    } finally {
      setExtractingId(null)
    }
  }

  const handleViewRequirements = async (tender) => {
    setSelectedTender(tender)
    setActivePanel('rules')
    setLoadingReqs(true)
    try {
      const res = await api.get(`/tenders/${tender.id}/requirements`)
      setRequirements(res.data)
    } catch (err) {
      console.error('Failed to load requirements:', err)
    } finally {
      setLoadingReqs(false)
    }
  }

  // 2. Vendor Documents Portal
  const handleOpenVendorDocs = async (tender) => {
    setSelectedTender(tender)
    setActivePanel('vendor')
    fetchVendorDocs(tender.id)
  }

  const fetchVendorDocs = async (tenderId) => {
    try {
      const res = await api.get(`/vendor-documents/${tenderId}`)
      setVendorDocs(res.data)
    } catch (err) {
      console.error('Failed to load vendor docs:', err)
    }
  }

  const handleVendorDocUpload = async (e) => {
    e.preventDefault()
    if (!vendorFile || !selectedTender) {
      setError('Please select a PDF document.')
      return
    }

    const formData = new FormData()
    formData.append('document_type', docType)
    formData.append('file', vendorFile)

    setUploadingVendorDoc(true)
    setError('')
    setSuccess('')

    try {
      await api.post(`/vendor-documents/${selectedTender.id}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setSuccess('Vendor proof document uploaded successfully.')
      setVendorFile(null)
      e.target.reset()
      fetchVendorDocs(selectedTender.id)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload vendor document.')
    } finally {
      setUploadingVendorDoc(false)
    }
  }

  // 3. AI Compliance Verification
  const handleRunCompliance = async (tender) => {
    setSelectedTender(tender)
    setActivePanel('compliance')
    setVerifyingId(tender.id)
    setLoadingCompliance(true)
    setError('')
    setSuccess('')
    try {
      const res = await api.post(`/compliance/verify/${tender.id}`)
      setComplianceResults(res.data)
      setSuccess(`Compliance verification completed across ${res.data.length} evaluation points.`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Compliance verification failed. Please ensure requirements are extracted first.')
    } finally {
      setVerifyingId(null)
      setLoadingCompliance(false)
    }
  }

  // 4. Authenticated Download PDF
  const handleDownloadPdf = async (tenderId) => {
    try {
      const response = await api.get(`/compliance/report/${tenderId}`, {
        responseType: 'blob',
      })
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `compliance_report_${tenderId}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('PDF download error:', err)
      setError('Failed to download compliance report.')
    }
  }

  return (
    <div style={{ maxWidth: '1100px', margin: '30px auto', padding: '0 20px', fontFamily: 'sans-serif' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '16px', borderBottom: '1px solid #e0e0e0' }}>
        <div>
          <h2 style={{ margin: 0, color: '#1a365d' }}>GeM Bid Compliance Verification</h2>
          <p style={{ margin: '4px 0 0', color: '#4a5568', fontSize: '14px' }}>Automated AI Verification & Audit Trail</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <span style={{ fontSize: '14px', color: '#2d3748' }}>User: <strong>{user?.email}</strong></span>
          <button
            onClick={logout}
            style={{ padding: '6px 14px', backgroundColor: '#e53e3e', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: '500' }}
          >
            Logout
          </button>
        </div>
      </div>

      {/* Upload Tender Card */}
      <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px', marginTop: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <h3 style={{ marginTop: 0, color: '#2d3748' }}>Upload Tender Document (PDF)</h3>

        {error && <div style={{ backgroundColor: '#fed7d7', color: '#9b2c2c', padding: '10px 12px', borderRadius: '4px', marginBottom: '14px', fontSize: '14px' }}>{error}</div>}
        {success && <div style={{ backgroundColor: '#c6f6d5', color: '#22543d', padding: '10px 12px', borderRadius: '4px', marginBottom: '14px', fontSize: '14px' }}>{success}</div>}

        <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', fontWeight: '500', color: '#4a5568' }}>Tender Title *</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Procurement of High-End Laptops for Lab"
              style={{ width: '100%', padding: '8px 10px', borderRadius: '4px', border: '1px solid #cbd5e0', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '15px' }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', fontWeight: '500', color: '#4a5568' }}>Tender Number (Optional)</label>
              <input
                type="text"
                value={tenderNumber}
                onChange={(e) => setTenderNumber(e.target.value)}
                placeholder="e.g. GEM/2026/B/99812"
                style={{ width: '100%', padding: '8px 10px', borderRadius: '4px', border: '1px solid #cbd5e0', boxSizing: 'border-box' }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', fontWeight: '500', color: '#4a5568' }}>Description (Optional)</label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Short description or notes"
                style={{ width: '100%', padding: '8px 10px', borderRadius: '4px', border: '1px solid #cbd5e0', boxSizing: 'border-box' }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', fontWeight: '500', color: '#4a5568' }}>Select PDF Document (Max 10MB) *</label>
            <input type="file" accept=".pdf,application/pdf" required onChange={handleFileChange} style={{ display: 'block' }} />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              alignSelf: 'flex-start',
              padding: '10px 20px',
              backgroundColor: loading ? '#a0aec0' : '#3182ce',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '15px',
              fontWeight: '600',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Uploading...' : 'Upload Tender'}
          </button>
        </form>
      </div>

      {/* Tender List Table */}
      <div style={{ marginTop: '30px' }}>
        <h3 style={{ color: '#2d3748', marginBottom: '12px' }}>Your Tender Documents</h3>
        {tenders.length === 0 ? (
          <p style={{ color: '#718096', fontSize: '14px' }}>No tender documents uploaded yet.</p>
        ) : (
          <div style={{ overflowX: 'auto', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
              <thead>
                <tr style={{ backgroundColor: '#edf2f7', borderBottom: '1px solid #e2e8f0', color: '#4a5568' }}>
                  <th style={{ padding: '12px 14px' }}>ID</th>
                  <th style={{ padding: '12px 14px' }}>Title</th>
                  <th style={{ padding: '12px 14px' }}>Status</th>
                  <th style={{ padding: '12px 14px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {tenders.map((t) => (
                  <tr key={t.id} style={{ borderBottom: '1px solid #edf2f7' }}>
                    <td style={{ padding: '10px 14px', color: '#718096' }}>#{t.id}</td>
                    <td style={{ padding: '10px 14px', fontWeight: '500', color: '#2d3748' }}>
                      {t.title}
                      {t.tender_number && <span style={{ display: 'block', fontSize: '12px', color: '#718096' }}>{t.tender_number}</span>}
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <span style={{
                        padding: '4px 8px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        backgroundColor: t.processing_status === 'PROCESSED' ? '#c6f6d5' : '#bee3f8',
                        color: t.processing_status === 'PROCESSED' ? '#22543d' : '#2b6cb0',
                        fontWeight: 'bold'
                      }}>
                        {t.processing_status}
                      </span>
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        <button
                          onClick={() => handleExtract(t)}
                          disabled={extractingId === t.id}
                          style={{ padding: '6px 10px', backgroundColor: '#319795', color: 'white', border: 'none', borderRadius: '4px', fontSize: '12px', cursor: 'pointer' }}
                        >
                          {extractingId === t.id ? 'Extracting...' : 'Extract Rules'}
                        </button>
                        <button
                          onClick={() => handleViewRequirements(t)}
                          style={{ padding: '6px 10px', backgroundColor: '#edf2f7', color: '#2d3748', border: '1px solid #cbd5e0', borderRadius: '4px', fontSize: '12px', cursor: 'pointer' }}
                        >
                          View Rules
                        </button>
                        <button
                          onClick={() => handleOpenVendorDocs(t)}
                          style={{ padding: '6px 10px', backgroundColor: '#4a5568', color: 'white', border: 'none', borderRadius: '4px', fontSize: '12px', cursor: 'pointer' }}
                        >
                          Vendor Docs
                        </button>
                        <button
                          onClick={() => handleRunCompliance(t)}
                          disabled={verifyingId === t.id}
                          style={{ padding: '6px 10px', backgroundColor: '#805ad5', color: 'white', border: 'none', borderRadius: '4px', fontSize: '12px', cursor: 'pointer', fontWeight: 'bold' }}
                        >
                          {verifyingId === t.id ? 'Verifying...' : 'Run Verification'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Action Panels */}
      {selectedTender && (
        <div style={{ marginTop: '30px' }}>
          {/* Rules Panel */}
          {activePanel === 'rules' && (
            <div style={{ border: '1px solid #cbd5e0', borderRadius: '8px', padding: '20px', backgroundColor: '#f7fafc' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <h3 style={{ margin: 0, color: '#1a202c' }}>
                  Extracted Rules for: <span style={{ color: '#2b6cb0' }}>{selectedTender.title}</span>
                </h3>
                <button onClick={() => setActivePanel(null)} style={{ background: 'none', border: 'none', fontSize: '16px', cursor: 'pointer', color: '#718096' }}>✕ Close</button>
              </div>

              {loadingReqs ? (
                <p style={{ color: '#718096' }}>Loading rules...</p>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px', backgroundColor: '#ffffff', borderRadius: '6px' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#edf2f7', borderBottom: '2px solid #cbd5e0' }}>
                      <th style={{ padding: '10px' }}>Category</th>
                      <th style={{ padding: '10px' }}>Requirement Clause</th>
                      <th style={{ padding: '10px' }}>Value</th>
                      <th style={{ padding: '10px' }}>Type</th>
                      <th style={{ padding: '10px' }}>Page</th>
                    </tr>
                  </thead>
                  <tbody>
                    {requirements.map((r) => (
                      <tr key={r.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                        <td style={{ padding: '10px', fontWeight: '600', color: '#2b6cb0' }}>{r.category}</td>
                        <td style={{ padding: '10px', color: '#2d3748' }}>{r.requirement_text}</td>
                        <td style={{ padding: '10px', fontWeight: '500' }}>{r.required_value ? `${r.required_value} ${r.unit || ''}` : 'Document Verification'}</td>
                        <td style={{ padding: '10px' }}>
                          <span style={{ padding: '2px 6px', borderRadius: '4px', fontSize: '11px', backgroundColor: r.mandatory ? '#fed7d7' : '#e2e8f0', color: r.mandatory ? '#9b2c2c' : '#4a5568', fontWeight: '600' }}>
                            {r.mandatory ? 'MANDATORY' : 'OPTIONAL'}
                          </span>
                        </td>
                        <td style={{ padding: '10px', color: '#718096' }}>Page {r.source_page || 1}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* Vendor Docs Panel */}
          {activePanel === 'vendor' && (
            <div style={{ border: '1px solid #cbd5e0', borderRadius: '8px', padding: '20px', backgroundColor: '#edf2f7' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <h3 style={{ margin: 0, color: '#1a202c' }}>
                  Vendor Documents for: <span style={{ color: '#2b6cb0' }}>{selectedTender.title}</span>
                </h3>
                <button onClick={() => setActivePanel(null)} style={{ background: 'none', border: 'none', fontSize: '16px', cursor: 'pointer', color: '#718096' }}>✕ Close</button>
              </div>

              <form onSubmit={handleVendorDocUpload} style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', backgroundColor: '#fff', padding: '14px', borderRadius: '6px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px' }}>Document Type</label>
                  <select value={docType} onChange={(e) => setDocType(e.target.value)} style={{ padding: '8px', borderRadius: '4px', border: '1px solid #cbd5e0' }}>
                    <option value="GST Certificate">GST Certificate</option>
                    <option value="Past Experience Certificate">Past Experience Certificate</option>
                    <option value="Annual Turnover / ITR">Annual Turnover / ITR</option>
                    <option value="ISO Certificate">ISO Certificate</option>
                    <option value="OEM Authorization">OEM Authorization</option>
                    <option value="General Document">General Document</option>
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px' }}>Select PDF File</label>
                  <input type="file" accept=".pdf,application/pdf" required onChange={(e) => setVendorFile(e.target.files[0])} />
                </div>
                <button type="submit" disabled={uploadingVendorDoc} style={{ alignSelf: 'flex-end', padding: '8px 16px', backgroundColor: '#2b6cb0', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: '600' }}>
                  {uploadingVendorDoc ? 'Uploading...' : 'Upload Vendor Doc'}
                </button>
              </form>

              {vendorDocs.length === 0 ? (
                <p style={{ color: '#718096', fontSize: '14px' }}>No vendor documents uploaded for this tender yet.</p>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px', backgroundColor: '#ffffff', borderRadius: '6px', overflow: 'hidden' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#e2e8f0', borderBottom: '1px solid #cbd5e0' }}>
                      <th style={{ padding: '10px' }}>ID</th>
                      <th style={{ padding: '10px' }}>Document Type</th>
                      <th style={{ padding: '10px' }}>Filename</th>
                      <th style={{ padding: '10px' }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {vendorDocs.map((doc) => (
                      <tr key={doc.id} style={{ borderBottom: '1px solid #edf2f7' }}>
                        <td style={{ padding: '10px', color: '#718096' }}>#{doc.id}</td>
                        <td style={{ padding: '10px', fontWeight: '600', color: '#2d3748' }}>{doc.document_type}</td>
                        <td style={{ padding: '10px', color: '#4a5568' }}>{doc.filename}</td>
                        <td style={{ padding: '10px' }}>
                          <span style={{ padding: '2px 8px', borderRadius: '12px', fontSize: '11px', backgroundColor: '#c6f6d5', color: '#22543d', fontWeight: 'bold' }}>
                            {doc.processing_status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* Compliance Matrix Panel */}
          {activePanel === 'compliance' && (
            <div style={{ border: '1px solid #b794f4', borderRadius: '8px', padding: '20px', backgroundColor: '#faf5ff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <h3 style={{ margin: 0, color: '#44337a' }}>
                      Compliance Verification Matrix: <span style={{ color: '#6b46c1' }}>{selectedTender.title}</span>
                    </h3>
                    <button
                      onClick={() => handleDownloadPdf(selectedTender.id)}
                      style={{
                        padding: '6px 12px',
                        backgroundColor: '#3182ce',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        cursor: 'pointer',
                      }}
                    >
                      Download Audit PDF
                    </button>
                  </div>
                  <p style={{ margin: '4px 0 0', color: '#6b46c1', fontSize: '13px' }}>
                    Evidence-backed audit decisions with clause and source page mapping
                  </p>
                </div>
                <button onClick={() => setActivePanel(null)} style={{ background: 'none', border: 'none', fontSize: '16px', cursor: 'pointer', color: '#718096' }}>✕ Close</button>
              </div>

              {loadingCompliance ? (
                <p style={{ color: '#6b46c1', fontWeight: '500' }}>Evaluating documents against clauses...</p>
              ) : complianceResults.length === 0 ? (
                <p style={{ color: '#718096', fontSize: '14px' }}>No compliance verification executed yet.</p>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px', backgroundColor: '#ffffff', borderRadius: '6px' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#e9d8fd', borderBottom: '2px solid #b794f4', color: '#322659' }}>
                        <th style={{ padding: '10px' }}>Category</th>
                        <th style={{ padding: '10px' }}>Clause</th>
                        <th style={{ padding: '10px' }}>Status</th>
                        <th style={{ padding: '10px' }}>Confidence</th>
                        <th style={{ padding: '10px' }}>Evidence / Source</th>
                        <th style={{ padding: '10px' }}>Decision Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {complianceResults.map((c) => {
                        let statusBg = '#fed7d7'
                        let statusColor = '#9b2c2c'
                        if (c.status === 'COMPLIANT') {
                          statusBg = '#c6f6d5'
                          statusColor = '#22543d'
                        } else if (c.status === 'NEEDS_REVIEW') {
                          statusBg = '#feebc8'
                          statusColor = '#7b341e'
                        }

                        return (
                          <tr key={c.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                            <td style={{ padding: '10px', fontWeight: '600', color: '#2b6cb0' }}>{c.category}</td>
                            <td style={{ padding: '10px', color: '#2d3748', maxWidth: '240px' }}>{c.requirement_text}</td>
                            <td style={{ padding: '10px' }}>
                              <span style={{
                                padding: '4px 8px',
                                borderRadius: '4px',
                                fontSize: '11px',
                                backgroundColor: statusBg,
                                color: statusColor,
                                fontWeight: 'bold',
                              }}>
                                {c.status}
                              </span>
                            </td>
                            <td style={{ padding: '10px', fontWeight: '600', color: '#4a5568' }}>
                              {Math.round(c.confidence * 100)}%
                            </td>
                            <td style={{ padding: '10px', color: '#4a5568' }}>
                              <div>{c.evidence || '—'}</div>
                              {c.evidence_page && (
                                <span style={{ fontSize: '11px', color: '#718096', display: 'block', marginTop: '2px' }}>
                                  Source: Page {c.evidence_page}
                                </span>
                              )}
                            </td>
                            <td style={{ padding: '10px', color: '#2d3748', fontSize: '12px', maxWidth: '200px' }}>
                              {c.reason}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}