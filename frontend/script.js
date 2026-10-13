// Global variables
let currentAnalysisId = null;
let statusInterval = null;

// DOM elements
const uploadSection = document.getElementById('upload-section');
const processingSection = document.getElementById('processing-section');
const reportSection = document.getElementById('report-section');
const errorSection = document.getElementById('error-section');

const dropZone = document.getElementById('drop-zone');
const imageInput = document.getElementById('image-input');
const selectButton = document.getElementById('select-button');
const imagePreview = document.getElementById('image-preview');
const previewImg = document.getElementById('preview-img');
const analyzeButton = document.getElementById('analyze-button');
const clearButton = document.getElementById('clear-button');
const newAnalysisButton = document.getElementById('new-analysis-button');
const retryButton = document.getElementById('retry-button');

// API base URL
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:8000'
    : '';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    checkApiHealth();
});

function setupEventListeners() {
    // File input events
    selectButton.addEventListener('click', () => imageInput.click());
    imageInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop events
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);
    
    // Button events
    analyzeButton.addEventListener('click', startAnalysis);
    clearButton.addEventListener('click', clearImage);
    newAnalysisButton.addEventListener('click', startNewAnalysis);
    retryButton.addEventListener('click', startNewAnalysis);
}

async function checkApiHealth() {
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        if (!response.ok) {
            showError('Backend service is unavailable. Please ensure the server is running.');
        }
    } catch (error) {
        showError('Cannot connect to backend service. Please check if the server is running on port 8000.');
    }
}

// File handling functions
function handleDragOver(e) {
    e.preventDefault();
    dropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFile(file) {
    // Validate file type
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        showError('Please select a valid image file (PNG, JPG, JPEG, or WEBP).');
        return;
    }
    
    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
        showError('File size must be less than 10MB.');
        return;
    }
    
    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
        previewImg.src = e.target.result;
        dropZone.style.display = 'none';
        imagePreview.style.display = 'block';
    };
    reader.readAsDataURL(file);
    
    // Store file for analysis
    imageInput.files = e.target ? e.target.files : createFileList([file]);
}

function createFileList(files) {
    const dt = new DataTransfer();
    files.forEach(file => dt.items.add(file));
    return dt.files;
}

function clearImage() {
    imageInput.value = '';
    previewImg.src = '';
    dropZone.style.display = 'block';
    imagePreview.style.display = 'none';
    hideAllSections();
    uploadSection.style.display = 'block';
}

// Analysis functions
async function startAnalysis() {
    const files = imageInput.files;
    if (files.length === 0) {
        showError('Please select an image first.');
        return;
    }
    
    try {
        analyzeButton.disabled = true;
        analyzeButton.textContent = 'Starting...';
        
        const formData = new FormData();
        formData.append('image', files[0]);
        
        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Analysis failed to start');
        }
        
        const data = await response.json();
        currentAnalysisId = data.analysis_id;
        
        showProcessingSection(data.analysis_id);
        startStatusPolling();
        
    } catch (error) {
        console.error('Analysis start error:', error);
        showError(`Failed to start analysis: ${error.message}`);
        analyzeButton.disabled = false;
        analyzeButton.textContent = 'Analyze Content';
    }
}

function showProcessingSection(analysisId) {
    hideAllSections();
    processingSection.style.display = 'block';
    
    document.getElementById('analysis-id').textContent = analysisId;
    document.getElementById('current-status').textContent = 'Starting analysis...';
    
    // Reset progress
    document.getElementById('progress-fill').style.width = '0%';
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active', 'completed');
    });
}

function startStatusPolling() {
    if (statusInterval) {
        clearInterval(statusInterval);
    }
    
    statusInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/analyze/${currentAnalysisId}`);
            
            if (!response.ok) {
                throw new Error('Failed to get status');
            }
            
            const data = await response.json();
            updateProcessingStatus(data);
            
            if (data.status === 'completed') {
                clearInterval(statusInterval);
                await showReport(data.analysis_id);
            } else if (data.status === 'failed') {
                clearInterval(statusInterval);
                showError(data.error || 'Analysis failed');
            }
            
        } catch (error) {
            console.error('Status polling error:', error);
            clearInterval(statusInterval);
            showError('Lost connection to analysis service');
        }
    }, 2000);
}

function updateProcessingStatus(data) {
    const status = data.status;
    const progress = data.progress || 0;
    
    // Update progress bar
    document.getElementById('progress-fill').style.width = `${progress}%`;
    
    // Update current status text
    const statusTexts = {
        'received': 'Image received successfully',
        'validating': 'Validating image format and content',
        'uploaded': 'Image uploaded and stored',
        'extracting': 'Extracting text and analyzing content',
        'analyzing': 'Performing content and claim analysis',
        'researching': 'Researching claims and gathering evidence',
        'verifying': 'Verifying evidence and calculating risk',
        'generating_report': 'Generating comprehensive report',
        'completed': 'Analysis completed successfully'
    };
    
    document.getElementById('current-status').textContent = 
        statusTexts[status] || `Status: ${status}`;
    
    // Update step indicators
    const steps = ['received', 'validating', 'uploaded', 'extracting', 'analyzing', 
                  'researching', 'verifying', 'generating_report', 'completed'];
    
    const currentIndex = steps.indexOf(status);
    
    document.querySelectorAll('.step').forEach((step, index) => {
        step.classList.remove('active', 'completed');
        
        if (index < currentIndex) {
            step.classList.add('completed');
        } else if (index === currentIndex) {
            step.classList.add('active');
        }
    });
}

// Report display functions
async function showReport(analysisId) {
    try {
        const response = await fetch(`${API_BASE}/api/report/${analysisId}`);
        
        if (!response.ok) {
            throw new Error('Failed to load report');
        }
        
        const reportData = await response.json();
        displayReport(reportData);
        
    } catch (error) {
        console.error('Report loading error:', error);
        showError(`Failed to load report: ${error.message}`);
    }
}

function displayReport(reportData) {
    hideAllSections();
    reportSection.style.display = 'block';
    
    // Report header
    document.getElementById('report-analysis-id').textContent = reportData.analysis_id;
    document.getElementById('report-timestamp').textContent = 
        new Date().toLocaleString();
    
    // Content analysis
    if (reportData.content) {
        document.getElementById('report-image').src = reportData.content.image_url || previewImg.src;
        document.getElementById('extracted-text').textContent = 
            reportData.content.extracted_text || 'No text extracted';
        document.getElementById('content-type').textContent = 
            reportData.content.content_type || 'Unknown';
        document.getElementById('content-category').textContent = 
            reportData.content.category || 'Uncategorized';
    }
    
    // Claims
    if (reportData.claim) {
        document.getElementById('main-claim').textContent = 
            reportData.claim.claim || 'No verifiable claim detected';
        document.getElementById('claim-type').textContent = 
            reportData.claim.claim_type || 'N/A';
        
        // Entities
        const entitiesContainer = document.getElementById('claim-entities');
        entitiesContainer.innerHTML = '';
        if (reportData.claim.entities && reportData.claim.entities.length > 0) {
            reportData.claim.entities.forEach(entity => {
                const span = document.createElement('span');
                span.textContent = entity;
                entitiesContainer.appendChild(span);
            });
        } else {
            entitiesContainer.textContent = 'None identified';
        }
        
        // Values
        const valuesContainer = document.getElementById('claim-values');
        valuesContainer.innerHTML = '';
        if (reportData.claim.values && reportData.claim.values.length > 0) {
            reportData.claim.values.forEach(value => {
                const span = document.createElement('span');
                span.textContent = value;
                valuesContainer.appendChild(span);
            });
        } else {
            valuesContainer.textContent = 'None identified';
        }
    }
    
    // Sentiment
    if (reportData.sentiment) {
        const sentimentLabel = document.getElementById('sentiment-label');
        const confidence = Math.round((reportData.sentiment.confidence || 0) * 100);
        
        sentimentLabel.textContent = (reportData.sentiment.label || 'Unknown').toUpperCase();
        sentimentLabel.className = `sentiment-label ${reportData.sentiment.label || 'neutral'}`;
        
        document.getElementById('sentiment-confidence').textContent = confidence;
        document.getElementById('confidence-fill').style.width = `${confidence}%`;
    }
    
    // Media analysis
    displayMediaAnalysis(reportData.media_analysis);
    
    // Research
    displayResearch(reportData.research);
    
    // Risk assessment
    displayRiskAssessment(reportData.risk_assessment);
    
    // AI Summary
    if (reportData.report) {
        document.getElementById('ai-summary').textContent = 
            reportData.report.summary || 'No summary available';
        document.getElementById('recommended-action').textContent = 
            reportData.report.recommended_action || 'No specific action recommended';
    }
    
    // Sources
    displaySources(reportData.research?.sources || []);
}

function displayMediaAnalysis(mediaAnalysis) {
    const container = document.getElementById('media-analysis-content');
    container.innerHTML = '';
    
    if (!mediaAnalysis) {
        container.innerHTML = '<p>Media analysis not available</p>';
        return;
    }
    
    const indicators = mediaAnalysis.indicators || [];
    
    if (indicators.length === 0) {
        container.innerHTML = '<p>No specific indicators detected</p>';
        return;
    }
    
    indicators.forEach(indicator => {
        const div = document.createElement('div');
        div.className = `media-indicator ${indicator.risk_level || 'low'}`;
        div.innerHTML = `
            <strong>${indicator.type || 'General'}:</strong> 
            ${indicator.description || 'No description available'}
        `;
        container.appendChild(div);
    });
}

function displayResearch(research) {
    if (!research) return;
    
    // Update counts
    document.getElementById('sources-count').textContent = research.total_sources || 0;
    document.getElementById('supporting-count').textContent = 
        (research.supporting_evidence || []).length;
    document.getElementById('contradicting-count').textContent = 
        (research.contradicting_evidence || []).length;
    
    // Supporting evidence
    const supportingContainer = document.getElementById('supporting-evidence');
    supportingContainer.innerHTML = '';
    
    if (research.supporting_evidence && research.supporting_evidence.length > 0) {
        research.supporting_evidence.forEach(evidence => {
            const div = document.createElement('div');
            div.className = 'evidence-item supporting';
            div.textContent = evidence.summary || evidence.title || 'Supporting evidence found';
            supportingContainer.appendChild(div);
        });
    } else {
        supportingContainer.innerHTML = '<p>No supporting evidence found</p>';
    }
    
    // Contradicting evidence
    const contradictingContainer = document.getElementById('contradicting-evidence');
    contradictingContainer.innerHTML = '';
    
    if (research.contradicting_evidence && research.contradicting_evidence.length > 0) {
        research.contradicting_evidence.forEach(evidence => {
            const div = document.createElement('div');
            div.className = 'evidence-item contradicting';
            div.textContent = evidence.summary || evidence.title || 'Contradicting evidence found';
            contradictingContainer.appendChild(div);
        });
    } else {
        contradictingContainer.innerHTML = '<p>No contradicting evidence found</p>';
    }
}

function displayRiskAssessment(riskAssessment) {
    if (!riskAssessment) return;
    
    const score = riskAssessment.score || 0;
    const level = riskAssessment.level || 'UNKNOWN';
    
    // Update score display
    const scoreElement = document.getElementById('risk-score');
    scoreElement.textContent = score;
    
    // Set score color based on value
    scoreElement.className = 'score-value';
    if (score <= 30) scoreElement.classList.add('low');
    else if (score <= 60) scoreElement.classList.add('medium');
    else if (score <= 80) scoreElement.classList.add('high');
    else scoreElement.classList.add('critical');
    
    // Update level display
    const levelElement = document.getElementById('risk-level');
    levelElement.textContent = level;
    levelElement.className = `risk-level ${level.toLowerCase()}`;
    
    // Update reasons
    const reasonsList = document.getElementById('risk-reasons-list');
    reasonsList.innerHTML = '';
    
    if (riskAssessment.reasons && riskAssessment.reasons.length > 0) {
        riskAssessment.reasons.forEach(reason => {
            const li = document.createElement('li');
            li.textContent = reason;
            reasonsList.appendChild(li);
        });
    } else {
        const li = document.createElement('li');
        li.textContent = 'No specific risk factors identified';
        reasonsList.appendChild(li);
    }
}

function displaySources(sources) {
    const container = document.getElementById('sources-list');
    container.innerHTML = '';
    
    if (!sources || sources.length === 0) {
        container.innerHTML = '<p>No external sources available</p>';
        return;
    }
    
    sources.forEach((source, index) => {
        const div = document.createElement('div');
        div.className = 'source-item';
        div.innerHTML = `
            <a href="${source.url || '#'}" target="_blank" rel="noopener noreferrer">
                ${source.title || `Source ${index + 1}`}
            </a>
            <div class="source-description">
                ${source.description || source.snippet || 'No description available'}
            </div>
        `;
        container.appendChild(div);
    });
}

// Utility functions
function hideAllSections() {
    uploadSection.style.display = 'none';
    processingSection.style.display = 'none';
    reportSection.style.display = 'none';
    errorSection.style.display = 'none';
}

function showError(message) {
    hideAllSections();
    errorSection.style.display = 'block';
    document.getElementById('error-message').textContent = message;
    
    // Reset analyze button
    analyzeButton.disabled = false;
    analyzeButton.textContent = 'Analyze Content';
}

function startNewAnalysis() {
    if (statusInterval) {
        clearInterval(statusInterval);
    }
    currentAnalysisId = null;
    clearImage();
}

// Handle page visibility change to pause/resume polling
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden, pause polling
        if (statusInterval) {
            clearInterval(statusInterval);
        }
    } else {
        // Page is visible, resume polling if analysis is in progress
        # Fix JavaScript visibility check
        if (currentAnalysisId && reportSection.style.display === 'none') {
            startStatusPolling();
        }
    }
});