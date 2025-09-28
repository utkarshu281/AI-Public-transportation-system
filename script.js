// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const searchForm = document.getElementById('searchForm');
const startLocationInput = document.getElementById('startLocation');
const destinationInput = document.getElementById('destination');
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');
const noResults = document.getElementById('noResults');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');
const busList = document.getElementById('busList');
const resultsCount = document.getElementById('resultsCount');

// Modal elements
const mapModal = document.getElementById('mapModal');
const trackedBusId = document.getElementById('trackedBusId');
const busSpeed = document.getElementById('busSpeed');
const busDirection = document.getElementById('busDirection');
const etaCountdown = document.getElementById('etaCountdown');
const lastUpdated = document.getElementById('lastUpdated');

// State
let currentSearchResults = [];
let map = null;
let busMarker = null;
let locationRefreshInterval = null;
let etaTimer = null;
let currentBusId = null;
let currentETA = null;

// Event Listeners
if (searchForm) {
    searchForm.addEventListener('submit', handleSearch);
}

// Handle search form submission
async function handleSearch(event) {
    event.preventDefault();
    
    const startLocation = startLocationInput.value.trim();
    const destination = destinationInput.value.trim();
    
    if (!startLocation || !destination) {
        showError('Please enter both start location and destination.');
        return;
    }
    
    if (startLocation === destination) {
        showError('Start location and destination cannot be the same.');
        return;
    }
    
    await searchBuses(startLocation, destination);
}

// Search for buses
async function searchBuses(startLocation, destination) {
    showLoading();
    hideResults();
    hideError();
    hideNoResults();
    
    try {
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/buses/available`, {
            method: 'POST',
            body: JSON.stringify({
                start_location: startLocation,
                destination: destination
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const buses = await response.json();
        
        if (buses.length === 0) {
            showNoResults();
        } else {
            currentSearchResults = buses;
            displayBusResults(buses);
        }
        
    } catch (err) {
        console.error('Search error:', err);
        showError(`Failed to search buses: ${err.message}`);
    } finally {
        hideLoading();
    }
}

// Display bus results
function displayBusResults(buses) {
    if (resultsCount) {
        resultsCount.textContent = buses.length;
    }
    
    if (busList) {
        busList.innerHTML = '';
        
        buses.forEach((bus, index) => {
            const busCard = createBusCard(bus, index);
            busList.appendChild(busCard);
        });
    }
    
    showResults();
}

// Create bus card element
function createBusCard(bus, index) {
    const card = document.createElement('div');
    card.className = 'bus-card';
    
    // Use crowd level from API or generate random
    const crowdLevel = bus.crowd_level || Math.floor(Math.random() * 5) + 1;
    const crowdDots = Array.from({length: 5}, (_, i) => 
        `<div class="crowd-dot ${i < crowdLevel ? 'active' : ''}"></div>`
    ).join('');
    
    // Use ETA from API or generate random
    const etaMinutes = bus.eta_minutes || Math.floor(Math.random() * 30) + 5;
    
    // Use current speed from API
    const currentSpeed = bus.current_speed || 0;
    
    card.innerHTML = `
        <div class="bus-header">
            <div class="bus-route">
                <i class="fas fa-bus"></i>
                <div class="route-info">
                    <h3>${bus.route_number}</h3>
                    <p>${bus.start_location} → ${bus.destination}</p>
                </div>
            </div>
            <div class="bus-id">${bus.bus_id}</div>
        </div>
        
        <div class="bus-details">
            <div class="detail-item">
                <div class="detail-label">Departure Time</div>
                <div class="detail-value">${bus.departure_time}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Arrival Time</div>
                <div class="detail-value">${bus.arrival_time}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Fare</div>
                <div class="detail-value">₹${bus.fare.toFixed(2)}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Available Seats</div>
                <div class="detail-value">${bus.available_seats}/${bus.capacity}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Current Speed</div>
                <div class="detail-value">
                    <span class="speed-badge">
                        <i class="fas fa-tachometer-alt"></i>
                        ${currentSpeed.toFixed(1)} km/h
                    </span>
                </div>
            </div>
            <div class="detail-item">
                <div class="detail-label">ETA</div>
                <div class="detail-value">
                    <span class="eta-badge">
                        <i class="fas fa-clock"></i>
                        ${etaMinutes} min
                    </span>
                </div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Crowd Level</div>
                <div class="detail-value">
                    <div class="crowd-level">
                        <span>${crowdLevel}/5</span>
                        <div class="crowd-indicator">
                            ${crowdDots}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="bus-actions">
            <button class="btn-track" onclick="trackBus('${bus.bus_id}')">
                <i class="fas fa-map-marked-alt"></i>
                Track Live
            </button>
            <button class="btn-eta" onclick="getDetailedETA('${bus.bus_id}')">
                <i class="fas fa-route"></i>
                Get ETA
            </button>
        </div>
    `;
    
    return card;
}

// Get detailed ETA for a bus
async function getDetailedETA(busId) {
    try {
        showNotification('Calculating detailed ETA...', 'info');
        
        const response = await makeAuthenticatedRequest(`${API_BASE_URL}/buses/${busId}/eta`, {
            method: 'POST',
            body: JSON.stringify({
                bus_id: busId,
                current_location: "Current Location",
                destination: destinationInput?.value || "Destination",
                traffic_conditions: "normal",
                passenger_count: 25
            })
        });
        
        if (response && response.ok) {
            const etaData = await response.json();
            
            // Show detailed ETA information
            showDetailedETAModal(etaData);
            
        } else {
            throw new Error('Failed to get ETA');
        }
    } catch (error) {
        console.error('ETA error:', error);
        showNotification('Failed to get detailed ETA', 'error');
    }
}

// Show detailed ETA modal
function showDetailedETAModal(etaData) {
    const modalContent = `
        <div class="eta-modal">
            <h3><i class="fas fa-clock"></i> Detailed ETA for ${etaData.bus_id}</h3>
            <div class="eta-details">
                <div class="eta-item">
                    <strong>Estimated Arrival:</strong> 
                    <span>${new Date(etaData.estimated_arrival_time).toLocaleTimeString()}</span>
                </div>
                <div class="eta-item">
                    <strong>Duration:</strong> 
                    <span>${Math.round(etaData.estimated_duration_minutes)} minutes</span>
                </div>
                <div class="eta-item">
                    <strong>Confidence:</strong> 
                    <span class="confidence-badge">${(etaData.confidence_score * 100).toFixed(0)}%</span>
                </div>
                <div class="eta-item">
                    <strong>Route:</strong> 
                    <span>${etaData.route_info.route_name}</span>
                </div>
                <div class="eta-item">
                    <strong>Total Stops:</strong> 
                    <span>${etaData.route_info.total_stops}</span>
                </div>
                <div class="factors">
                    <strong>Factors Considered:</strong>
                    <ul>
                        ${etaData.factors_considered.map(factor => `<li>${factor}</li>`).join('')}
                    </ul>
                </div>
            </div>
            <button class="btn btn-primary" onclick="closeETAModal()">Close</button>
        </div>
    `;
    
    // Create and show modal
    let etaModal = document.getElementById('eta-detail-modal');
    if (!etaModal) {
        etaModal = document.createElement('div');
        etaModal.id = 'eta-detail-modal';
        etaModal.className = 'modal';
        etaModal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        `;
        document.body.appendChild(etaModal);
    }
    
    etaModal.innerHTML = `
        <div class="modal-content" style="background: white; padding: 30px; border-radius: 15px; max-width: 500px; width: 90%;">
            ${modalContent}
        </div>
    `;
    etaModal.style.display = 'flex';
    
    showNotification('ETA calculated successfully!', 'success');
}

// Close ETA modal
function closeETAModal() {
    const etaModal = document.getElementById('eta-detail-modal');
    if (etaModal) {
        etaModal.style.display = 'none';
    }
}

// Track bus function with enhanced features
async function trackBus(busId) {
    try {
        showNotification('Loading bus location...', 'info');
        
        // Get enhanced bus location
        const locationResponse = await makeAuthenticatedRequest(`${API_BASE_URL}/buses/${busId}/location`);
        if (!locationResponse || !locationResponse.ok) {
            throw new Error('Failed to get bus location');
        }
        
        const location = await locationResponse.json();
        
        // Store current bus ID and ETA
        currentBusId = busId;
        currentETA = Math.floor(Math.random() * 30) + 5; // Will be replaced with actual ETA
        
        // Update modal with enhanced bus information
        if (trackedBusId) trackedBusId.textContent = busId;
        if (busSpeed) busSpeed.textContent = `${location.speed.toFixed(1)} km/h`;
        if (busDirection) busDirection.textContent = location.direction;
        if (lastUpdated) lastUpdated.textContent = new Date(location.last_updated).toLocaleTimeString();
        
        // Initialize map if not already done
        if (!map) {
            initializeMap(location.latitude, location.longitude);
        } else {
            // Update existing map
            updateMapLocation(location.latitude, location.longitude, location.speed, location.direction);
        }
        
        // Start ETA countdown
        startETACountdown();
        
        // Start location refresh with enhanced data
        startLocationRefresh();
        
        // Show modal
        showMapModal();
        
        showNotification('Bus tracking started!', 'success');
        
    } catch (err) {
        console.error('Track bus error:', err);
        showError(`Failed to track bus: ${err.message}`);
    }
}

// Enhanced map initialization
function initializeMap(lat, lng) {
    setTimeout(() => {
        if (typeof L === 'undefined') {
            console.error('Leaflet library not loaded');
            showNotification('Map service unavailable', 'error');
            return;
        }
        
        map = L.map('map').setView([lat, lng], 13);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        
        // Enhanced bus marker
        busMarker = L.marker([lat, lng], {
            icon: L.divIcon({
                className: 'bus-marker',
                html: '<i class="fas fa-bus" style="color: #667eea; font-size: 20px;"></i>',
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        }).addTo(map);
        
        // Enhanced popup
        busMarker.bindPopup(`
            <div style="text-align: center;">
                <strong>Bus ${currentBusId}</strong><br>
                Speed: ${busSpeed?.textContent || 'N/A'}<br>
                Direction: ${busDirection?.textContent || 'N/
