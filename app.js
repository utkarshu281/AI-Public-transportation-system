//import React, { useState, useEffect, useCallback, useMemo } from 'react';

// --- Global Constants (Simulating external data and structure) ---

const MOCK_STOPS = [
  'Town Hall', 'Main Market', 'University Gate', 'Hospital Square', 'Railway Station'
];
const INITIAL_START = 'Town Hall';
const INITIAL_END = 'University Gate';

// Full route metadata structure, necessary for the Bus Details Screen UI
const ROUTE_METADATA = {
    "Route-1": {
        "name": "City Center to University Loop",
        "stops": [
            {"name": "Town Hall", "lat": 26.918, "lon": 75.790, "index": 0},
            {"name": "Main Market", "lat": 26.925, "lon": 75.795, "index": 1},
            {"name": "University Gate", "lat": 26.932, "lon": 75.785, "index": 2},
            {"name": "Hospital Square", "lat": 26.920, "lon": 75.778, "index": 3}
        ]
    },
    "Route-2": {
        "name": "Railway Station Shuttle",
        "stops": [
            {"name": "Railway Station", "lat": 26.910, "lon": 75.805, "index": 0},
            {"name": "Industrial Area", "lat": 26.900, "lon": 75.815, "index": 1},
            {"name": "Airport Road", "lat": 26.895, "lon": 75.800, "index": 2}
        ]
    }
};

const INITIAL_FAVORITES = [
    { name: "Home → College", route: "Route-1", start: "Town Hall", end: "University Gate", bus_id: "Bus-1" },
    { name: "Office Trip", route: "Route-2", start: "Railway Station", end: "Airport Road", bus_id: "Bus-2" },
];

const PASSKEY_MAP = {
    'user': '1',
    'admin': '2',
    'driver': '3' // Added driver role for explicit login as well
};


// --- Utility Functions ---

/**
 * Mocks the fetch operation with retry and backoff logic for SIH environment.
 * @param {string} url - The API endpoint to fetch.
 * @param {boolean} isPlan - If true, handles the route planning response structure.
 * @returns {Promise<any>}
 */
const reliableFetch = async (url, isPlan = false) => {
  const MAX_RETRIES = 3;
  let error = null;

  for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
    try {
      // Added a slight delay to simulate network latency in low-bandwidth areas
      await new Promise(resolve => setTimeout(resolve, 300)); 
      
      // FIX: Ensure URL is fully parsed and encoded before fetch (if not already)
      const encodedUrl = new URL(url.startsWith('http') ? url : window.location.origin + url).toString();
      
      const response = await fetch(encodedUrl);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      
      // Data sanity check for plan endpoint
      if (isPlan) {
         if (data.error) throw new Error(data.error); 
         if (!data.suggestions) data.suggestions = []; // Ensure suggestions array exists
      }
      
      return data;
    } catch (e) {
      error = e;
      console.warn(`Fetch attempt ${attempt + 1} failed for ${url}. Retrying...`, e);
      if (attempt < MAX_RETRIES - 1) {
        // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
      }
    }
  }
  throw error; // Throw after all retries fail
};


// --- Component 1: Route Planner (Home Screen + Search) ---

const RouteSearchUI = ({ setAppState, start, setStart, end, setEnd, handleSearch, isLoading, error, isSearching, suggestions, handleSelectBus }) => {
    
    const MockMap = () => (
        <div className="bg-gray-200 h-40 rounded-xl shadow-inner flex items-center justify-center border border-gray-300">
            <div className="text-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-500 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.828 0l-4.243-4.243m-4.243 2.828a4 4 0 000 5.656h8.485a4 4 0 005.657-5.657M12 12a4 4 0 100-8 4 4 0 000 8z"/></svg>
                <p className="text-sm text-gray-600 mt-1">Real-Time Map View (Simulated)</p>
            </div>
        </div>
    );
    
    const RenderContent = () => {
        if (isLoading) {
            return <p className="text-center text-blue-600 p-4">Loading routes...</p>;
        }
        
        if (isSearching && suggestions.length > 0) {
            return (
                <div className="space-y-3 pt-4">
                    <h3 className="font-semibold text-gray-700">🚌 Routes from {start} to {end}</h3>
                    {suggestions.map((s, index) => (
                        <div 
                            key={index} 
                            onClick={() => handleSelectBus(s)}
                            className="p-3 bg-white border-l-4 border-blue-500 shadow-md rounded-xl cursor-pointer hover:bg-blue-50 transition duration-150 transform hover:scale-[1.01]"
                        >
                            <div className="flex justify-between items-center">
                                <div className="flex flex-col">
                                    <p className="font-bold text-lg text-gray-900">{s.route_id} ({s.bus_id})</p>
                                    <p className="text-xs text-gray-600">Total Trip: {s.total_journey_min.split('.')[0]} min</p>
                                    <p className="text-xs text-gray-600">Fare: ₹20 (Mock)</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-3xl font-extrabold text-green-600 leading-none">{s.eta_to_start_min.split('.')[0]}</p>
                                    <p className="text-xs text-gray-500 -mt-1">ETA MIN</p>
                                    <button className="mt-1 text-xs text-white bg-blue-500 py-1 px-2 rounded-full shadow-md">Track Live</button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            );
        }
        
        return <p className="text-center text-gray-500 p-4">No suggestions yet. Use the search bar above.</p>;
      };


    return (
        <div className="p-4 space-y-4">
            <div className="flex flex-col space-y-3 p-4 bg-gray-50 shadow-inner rounded-xl border">
                <div className='flex space-x-2'>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                    <h2 className="text-xl font-bold text-gray-800">Route Planner</h2>
                </div>
                
                <select 
                value={start} 
                onChange={(e) => setStart(e.target.value)}
                className="p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 text-sm appearance-none bg-white pr-8"
                >
                {MOCK_STOPS.map(stop => <option key={stop} value={stop}>{`📍 ${stop} (Start)`}</option>)}
                </select>
                
                <select 
                value={end} 
                onChange={(e) => setEnd(e.target.value)}
                className="p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 text-sm appearance-none bg-white pr-8"
                >
                {MOCK_STOPS.map(stop => <option key={stop} value={stop}>{`🏁 ${stop} (Destination)`}</option>)}
                </select>

                <button 
                onClick={handleSearch} 
                disabled={isLoading}
                className="p-3 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 transition duration-150 disabled:bg-blue-300 text-sm transform hover:scale-[1.01] active:scale-100"
                >
                {isLoading ? 'Searching...' : 'Find Routes'}
                </button>
            </div>

            {error && <p className="text-center text-red-500 font-medium">{error}</p>}
            
            <MockMap />
            
            <div className='flex justify-between space-x-2 mt-4'>
                <button onClick={() => setAppState('DRIVER_PANEL')} className='flex-1 p-2 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded-lg shadow-sm hover:shadow-md'>Track My Bus (Driver)</button>
                <button onClick={() => setAppState('ADMIN_PANEL')} className='flex-1 p-2 bg-red-100 text-red-800 text-xs font-semibold rounded-lg shadow-sm hover:shadow-md'>Nearby Stops (Admin)</button>
                <button onClick={() => setAppState('PROFILE')} className='flex-1 p-2 bg-purple-100 text-purple-800 text-xs font-semibold rounded-lg shadow-sm hover:shadow-md'>Saved Routes</button>
            </div>

            <RenderContent />
            
        </div>
    );
};

const RoutePlanner = ({ setAppState, setJourneyData }) => {
    const [start, setStart] = useState(INITIAL_START);
    const [end, setEnd] = useState(INITIAL_END);
    const [suggestions, setSuggestions] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isSearching, setIsSearching] = useState(false); 
    
    const handleSearch = useCallback(async () => {
        if (!start || !end) {
            setError("Please select both a Start and Destination.");
            return;
        }
        setIsLoading(true);
        setError(null);
        setSuggestions([]);
        
        const encodedStart = encodeURIComponent(start);
        const encodedEnd = encodeURIComponent(end);

        try {
            const data = await reliableFetch(`/api/v1/plan?start=${encodedStart}&end=${encodedEnd}`, true);

            if (data.error) {
                setError(`API Error: ${data.error}`);
            } else if (data.suggestions.length === 0) {
                setError(`No direct routes found from ${start} to ${end}.`);
            } else {
                setSuggestions(data.suggestions);
            }

        } catch (e) {
            setError("Failed to fetch route suggestions. Check API status (Python server).");
            console.error(e);
        } finally {
            setIsLoading(false);
            setIsSearching(true);
        }
    }, [start, end]);

    useEffect(() => {
        handleSearch();
    }, [handleSearch]);

    const handleSelectBus = (suggestion) => {
        setJourneyData({...suggestion, startStop: start, endStop: end, currentStop: suggestion.currentStop || start}); 
        setAppState('LIVE_TRACKING');
    };

    return (
        <RouteSearchUI
            start={start} setStart={setStart}
            end={end} setEnd={setEnd}
            handleSearch={handleSearch}
            isLoading={isLoading}
            error={error}
            isSearching={isSearching}
            suggestions={suggestions}
            handleSelectBus={handleSelectBus}
            setAppState={setAppState}
        />
    );
};

// --- Component 2: Live Tracking Screen (Step 4) ---

const LiveTrackerUI = ({ journeyData, setJourneyData, setAppState, liveBusInfo, isLoading, isFinalStop, isAlertActive, setIsNotificationEnabled, isNotificationEnabled, stopsRemainingToDest, currentStopIndex, destinationIndex, journeyStops, FinalAlert }) => {
    const MockLiveMap = () => (
        <div className="bg-gray-200 h-40 rounded-xl shadow-inner flex items-center justify-center border border-gray-300">
            <div className="text-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-500 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.828 0l-4.243-4.243m-4.243 2.828a4 4 0 000 5.656h8.485a4 4 0 005.657-5.657M12 12a4 4 0 100-8 4 4 0 000 8z"/></svg>
                <p className="text-sm text-gray-700 mt-1">Live Map of Route Line & Moving Bus</p>
            </div>
        </div>
    );
  
    const TimelineView = () => (
        <div className="mt-4 p-4 bg-white rounded-xl shadow-lg space-y-4">
            <h3 className="font-bold text-lg text-gray-800 border-b pb-2 mb-3">Timeline: Remaining Journey</h3>
            
            <div className='space-y-2 relative'>
                <div className='absolute left-3 top-0 bottom-0 w-1 bg-gray-300'></div>
                
                {journeyStops.slice(currentStopIndex).map((stop, index) => {
                    const isCurrent = index === 0;
                    const isDest = stop === journeyData.endStop;
                    const mockETA = isCurrent ? 0 : (stopsRemainingToDest - index) * 4 + 1;

                    return (
                        <div key={stop} className="flex items-start pl-8 relative">
                            <div className={`w-4 h-4 rounded-full border-4 absolute left-1 -mt-0.5 ${isCurrent ? 'bg-blue-600 border-blue-200 animate-pulse' : isDest ? 'bg-red-600 border-red-200' : 'bg-white border-gray-400'}`}></div>
                            
                            <div className="flex-1 -mt-1">
                                <p className={`font-semibold ${isCurrent ? 'text-blue-600' : isDest ? 'text-red-600' : 'text-gray-800'}`}>
                                    {stop} {isDest && " (Destination)"}
                                </p>
                                <p className="text-sm text-gray-500 -mt-0.5">
                                    {isCurrent ? 'Current Stop' : `ETA: ${mockETA} minutes`}
                                </p>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );

    return (
        <div className="p-4">
            <button 
                onClick={() => setAppState('PLANNER')} 
                className="text-sm text-gray-500 hover:text-blue-600 flex items-center p-2 rounded-lg bg-gray-100 mb-3 transition duration-150"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                Back to Search
            </button>

            <h1 className="text-xl font-extrabold text-center text-gray-800 mb-4">
                {journeyData.route_id} Tracker
            </h1>
            
            {isAlertActive && <FinalAlert isFinalStop={isFinalStop} stopsRemainingToDest={stopsRemainingToDest} endStop={journeyData.endStop} />}
            
            <MockLiveMap />
            
            <div className='flex justify-between items-center bg-gray-50 p-3 rounded-xl mt-4 shadow-sm'>
                <label htmlFor="alert-toggle" className='text-sm font-semibold text-gray-700'>
                    Alert me when bus is 2 stops away
                </label>
                <input 
                    type="checkbox" 
                    id="alert-toggle"
                    checked={isNotificationEnabled}
                    onChange={() => setIsNotificationEnabled(!isNotificationEnabled)}
                    className="h-5 w-5 text-blue-600 border-gray-300 rounded"
                />
            </div>

            <TimelineView />

            {isLoading && (
                <div className="mt-4 text-center text-gray-500">
                    <svg className="animate-spin h-5 w-5 mr-3 inline-block" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25"></circle><path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    Loading live updates...
                </div>
            )}
        </div>
    );
};

const FinalAlert = ({ isFinalStop, stopsRemainingToDest, endStop }) => (
    <div className="p-4 bg-red-100 border-l-4 border-red-500 text-red-700 font-semibold rounded-lg mt-4 shadow-md transition-all duration-500 animate-pulse">
        {isFinalStop ? 
            "🎉 ARRIVED! Please exit the bus safely." :
            `🔔 ALERT: Destination (${endStop}) is ${stopsRemainingToDest - 1} stop(s) away. Get ready!`
        }
    </div>
);


const LiveTracker = ({ journeyData, setJourneyData, setAppState }) => {
    const [liveBusInfo, setLiveBusInfo] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isAlertActive, setIsAlertActive] = useState(false);
    const [isNotificationEnabled, setIsNotificationEnabled] = useState(false);

    const routeDetail = ROUTE_METADATA[journeyData.route_id];
    const journeyStops = useMemo(() => routeDetail ? routeDetail.stops.map(s => s.name) : [], [routeDetail]);
    
    const currentStopIndex = journeyStops.findIndex(s => s === journeyData.currentStop);
    const destinationIndex = journeyStops.findIndex(s => s === journeyData.endStop);
    const nextStop = journeyStops[currentStopIndex + 1];
    const stopsRemainingToDest = destinationIndex - currentStopIndex;
    const isFinalStop = currentStopIndex >= destinationIndex;


    useEffect(() => {
        let intervalId;
        
        if (isFinalStop) {
            setIsLoading(false);
            setIsAlertActive(true);
            return;
        }

        const fetchLiveBusData = async () => {
            try {
                const allStatus = await reliableFetch(`/api/v1/status`);
                const bus = allStatus.find(b => b.bus_id === journeyData.bus_id);

                if (bus) {
                    if ((journeyData.updateCount || 0) % 3 === 0 && nextStop && currentStopIndex < destinationIndex) {
                        setJourneyData(prev => ({
                            ...prev,
                            currentStop: nextStop,
                            updateCount: (prev.updateCount || 0) + 1,
                        }));
                        if (isNotificationEnabled && stopsRemainingToDest === 3) { 
                            console.log(`Bus Alert: Your bus is 2 stops away from ${journeyData.endStop}!`);
                        }
                    } else {
                        setJourneyData(prev => ({ ...prev, updateCount: (prev.updateCount || 0) + 1 }));
                    }
                    
                    setLiveBusInfo(bus);
                    setIsLoading(false);
                }
            } catch (e) {
                console.error("Live fetch failed, attempting offline mode.");
                setIsLoading(false);
            }
        };
        
        if (journeyData.updateCount === undefined) {
            setJourneyData(prev => ({ ...prev, updateCount: 0 }));
        }

        intervalId = setInterval(fetchLiveBusData, 7000); 

        return () => clearInterval(intervalId);
    }, [journeyData, isFinalStop, nextStop, stopsRemainingToDest, isNotificationEnabled, setJourneyData, currentStopIndex, destinationIndex]);

    return (
        <LiveTrackerUI
            journeyData={journeyData} 
            setJourneyData={setJourneyData} 
            setAppState={setAppState} 
            liveBusInfo={liveBusInfo} 
            isLoading={isLoading} 
            isFinalStop={isFinalStop}
            isAlertActive={isAlertActive}
            setIsNotificationEnabled={setIsNotificationEnabled}
            isNotificationEnabled={isNotificationEnabled}
            stopsRemainingToDest={stopsRemainingToDest}
            currentStopIndex={currentStopIndex}
            destinationIndex={destinationIndex}
            journeyStops={journeyStops}
            FinalAlert={FinalAlert}
        />
    );
};


// --- Component 3: Favorites Screen (Step 5) ---

const ProfileScreen = ({ setAppState }) => {
    const [favorites, setFavorites] = useState(INITIAL_FAVORITES);

    return (
        <div className="p-4 space-y-4">
            <h2 className="text-xl font-bold text-gray-800 border-b pb-2">⭐ Saved Routes</h2>
            <div className="space-y-3">
                <p className="text-sm text-gray-600">Tap a route to track the bus instantly.</p>
                {favorites.map((fav, index) => (
                    <div key={index} className="p-3 bg-purple-50 border-l-4 border-purple-400 rounded-lg shadow-sm cursor-pointer hover:bg-purple-100 transition duration-150 transform hover:scale-[1.01]">
                        <p className="font-semibold text-purple-700">{fav.name}</p>
                        <p className="text-xs text-gray-600">{fav.route}: {fav.start} → {fav.end}</p>
                    </div>
                ))}
            </div>
            <button 
                onClick={() => setAppState('PLANNER')}
                className="w-full p-3 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 transition duration-150 text-sm transform hover:scale-[1.01]"
            >
                Back to Search
            </button>
        </div>
    );
}

// --- Component 4: Settings/Profile (Step 6) ---

const SettingsScreen = ({ setAppState }) => {
    const [language, setLanguage] = useState('English');
    
    return (
        <div className="p-4 space-y-6">
            <h2 className="text-xl font-bold text-gray-800 border-b pb-2">⚙️ Settings & Profile</h2>

            <div className='space-y-2'>
                <label className='font-semibold text-gray-700'>Language</label>
                <select value={language} onChange={(e) => setLanguage(e.target.value)} className="w-full p-3 border rounded-lg text-sm appearance-none bg-white pr-8">
                    <option value="English">English (Standard)</option>
                    <option value="Hindi">हिन्दी (Hindi)</option>
                    <option value="Marathi">मराठी (Marathi - Mock)</option>
                </select>
            </div>
            
            <div className='space-y-2'>
                 <label className='font-semibold text-gray-700'>Send Feedback</label>
                 <textarea placeholder="Tell us how we can improve..." rows="3" className='w-full p-3 border rounded-lg text-sm focus:ring-blue-500'></textarea>
                 <button className='w-full p-3 bg-green-500 text-white font-semibold rounded-lg hover:bg-green-600 text-sm transform hover:scale-[1.01]'>Submit Feedback</button>
            </div>


            <button onClick={() => setAppState('PLANNER')} className="w-full p-3 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 transition duration-150 text-sm transform hover:scale-[1.01]">Back to Home</button>
        </div>
    );
}

// --- Component 5: Driver Panel ---

const DriverPanel = ({ setAppState }) => {
    const [selectedBus, setSelectedBus] = useState('Bus-1');
    const [crowdedness, setCrowdedness] = useState('LIGHT');
    const [isSending, setIsSending] = useState(false);
    
    const handleUpdate = async (payload) => {
        setIsSending(true);
        try {
            const response = await fetch('/api/admin/bus-update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bus_id: selectedBus, crowdedness_level: crowdedness, ...payload })
            });
            const data = await response.json();
            alert(`Status updated for ${selectedBus}: ${data.status}`);
        } catch (error) {
            alert("Error updating status. Check Python backend.");
        } finally {
            setIsSending(false);
        }
    };
    
    return (
        <div className="p-4 space-y-4">
            <h2 className="text-xl font-bold text-gray-800 border-b pb-2">🧑‍🔧 Driver App</h2>
            
            <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-200 space-y-3 shadow-md">
                <label className='font-semibold text-gray-700'>Select Bus:</label>
                <select value={selectedBus} onChange={(e) => setSelectedBus(e.target.value)} className="w-full p-2 border rounded-lg text-sm appearance-none bg-white pr-8">
                    {['Bus-1', 'Bus-2', 'Bus-3', 'Bus-4', 'Bus-5', 'Bus-6', 'Bus-7', 'Bus-8', 'Bus-9', 'Bus-10', 'Bus-11', 'Bus-12', 'Bus-13', 'Bus-14', 'Bus-15'].map(id => <option key={id} value={id}>{id}</option>)}
                </select>
                
                <div className='flex space-x-2'>
                    <button onClick={() => handleUpdate({ is_running: true, status_message: "On-time" })} disabled={isSending} className="flex-1 p-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 disabled:bg-green-300 text-sm transform hover:scale-[1.02]">Start Trip</button>
                    <button onClick={() => handleUpdate({ is_running: false, status_message: "Trip Finished" })} disabled={isSending} className="flex-1 p-3 bg-red-600 text-white font-semibold rounded-lg hover:bg-red-700 disabled:bg-red-300 text-sm transform hover:scale-[1.02]">Stop Trip</button>
                </div>

                <label className='font-semibold text-gray-700'>Crowdedness:</label>
                <select value={crowdedness} onChange={(e) => setCrowdedness(e.target.value)} className="w-full p-2 border rounded-lg text-sm appearance-none bg-white pr-8">
                    <option value="LIGHT">Seats Available</option>
                    <option value="MODERATE">Standing Room Only</option>
                    <option value="HEAVY">Full</option>
                </select>
                <button onClick={() => handleUpdate({})} disabled={isSending} className="w-full p-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-blue-300 text-sm mt-2 transform hover:scale-[1.02]">Update Crowdedness</button>

            </div>
            
            <button onClick={() => setAppState('PLANNER')} className="w-full p-3 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 transition duration-150 text-sm transform hover:scale-[1.01]">Back to Home</button>
        </div>
    );
};

// --- Component 6: Admin Panel ---

const AdminPanel = ({ setAppState }) => {
    const [analytics, setAnalytics] = useState(null);
    
    useEffect(() => {
        const fetchAnalytics = async () => {
            try {
                const data = await reliableFetch('/api/v1/analytics');
                setAnalytics(data);
            } catch (e) {
                setAnalytics({ error: "Failed to load analytics." });
            }
        };
        fetchAnalytics();
    }, []);

    const statCard = (title, value, color) => (
        <div className={`p-4 ${color} rounded-lg shadow-md`}>
            <p className="text-sm font-medium text-gray-700">{title}</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
    );

    return (
        <div className="p-4 space-y-6">
            <h2 className="text-xl font-bold text-gray-800 border-b pb-2">🔑 Admin Dashboard Mock</h2>
            
            {/* Analytics Section */}
            <div className='space-y-3'>
                <h3 className="font-semibold text-gray-700">Analytics & Stats</h3>
                {analytics && !analytics.error ? (
                    <div className='grid grid-cols-2 gap-4'>
                        {statCard("Total Trips", analytics.total_trips, "bg-green-100")}
                        {statCard("Avg Delay", `${analytics.avg_delay_minutes} min`, "bg-red-100")}
                        {statCard("Busiest Route", analytics.busiest_route, "bg-blue-100")}
                        {statCard("Total Passengers", analytics.total_passengers, "bg-yellow-100")}
                    </div>
                ) : (
                    <p className="text-red-500 text-sm">{analytics?.error || "Loading..."}</p>
                )}
            </div>

            {/* Live Monitoring Mock */}
            <div className='space-y-3'>
                <h3 className="font-semibold text-gray-700">Live Monitoring (Simulated)</h3>
                <p className="text-xs text-gray-500">Go to Driver Panel to update bus status.</p>
                <div className="p-4 bg-white rounded-lg border shadow-md">
                    <p className="text-sm font-semibold">Bus-2 Status: <span className="text-green-600">ON ROUTE</span></p>
                    <p className="text-xs text-gray-600">Last Report: Main Market, Crowdedness: MODERATE</p>
                </div>
            </div>
            
            <button onClick={() => setAppState('PLANNER')} className="w-full p-3 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 transition duration-150 text-sm transform hover:scale-[1.01]">Back to Home</button>
        </div>
    );
};

// --- Component 7: Login Screen (NEW) ---

const LoginScreenUI = ({ username, setUsername, passkey, setPasskey, handleLogin, error, setAppState }) => {
    return (
        <div className="min-h-[600px] flex items-center justify-center p-4">
            <div className="w-full bg-white p-6 rounded-xl shadow-lg border border-gray-100 space-y-4 transform transition duration-300 hover:shadow-2xl">
                <h2 className="text-2xl font-bold text-center text-blue-600">Secure Access</h2>
                <p className="text-center text-sm text-gray-500">Enter your credentials to continue.</p>
                
                <input
                    type="text"
                    placeholder="Username (e.g., user, admin)"
                    value={username}
                    onChange={(e) => { setUsername(e.target.value); setError(null); }}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 text-sm transition duration-150"
                />
                <input
                    type="password"
                    placeholder="Passkey (e.g., 1, 2, 3)"
                    value={passkey}
                    onChange={(e) => { setPasskey(e.target.value); setError(null); }}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 text-sm transition duration-150"
                />

                {error && <p className="text-red-500 text-center text-sm font-medium bg-red-50 p-2">{error}</p>}
            </div>
        </div>
    );
};
// ...existing code...

// ...existing code...

// ...existing code...

const App = () => {
    const [appState, setAppState] = React.useState('LOGIN');
    const [username, setUsername] = React.useState('');
    const [passkey, setPasskey] = React.useState('');
    const [error, setError] = React.useState(null);
    const [journeyData, setJourneyData] = React.useState(null);
    const [isBusBoarded, setIsBusBoarded] = React.useState(false);

    const handleLogin = () => {
        if (username === 'user' && passkey === '1') {
            setAppState('USER_PANEL');
        } else if (username === 'admin' && passkey === '2') {
            setAppState('DRIVER_PANEL');
        } else {
            setError('Invalid credentials. Try again.');
        }
    };

    // User Panel: Route Planner → Live Tracking → Journey Screen
    if (appState === 'USER_PANEL') {
        if (!journeyData) {
            return (
                <RoutePlanner
                    setAppState={() => setAppState('USER_PANEL')}
                    setJourneyData={setJourneyData}
                />
            );
        } else if (!isBusBoarded) {
            return (
                <LiveTracker
                    journeyData={journeyData}
                    setJourneyData={setJourneyData}
                    setAppState={setAppState}
                >
                    <button
                        className="mt-4 p-2 bg-green-600 text-white rounded"
                        onClick={() => setIsBusBoarded(true)}
                    >
                        Board Bus
                    </button>
                </LiveTracker>
            );
        } else {
            return (
                <JourneyScreen
                    journeyData={journeyData}
                    setAppState={setAppState}
                />
            );
        }
    }

    // Driver Panel
    if (appState === 'DRIVER_PANEL') {
        return <DriverPanel setAppState={setAppState} />;
    }

    // Admin Panel (add your logic if needed)
    if (appState === 'ADMIN_PANEL') {
        return <AdminPanel setAppState={setAppState} />;
    }

    // Login Screen
    return (
        <LoginScreenUI
            username={username}
            setUsername={setUsername}
            passkey={passkey}
            setPasskey={setPasskey}
            handleLogin={handleLogin}
            error={error}
            setAppState={setAppState}
        />
    );
};

// Add a simple JourneyScreen component
const JourneyScreen = ({ journeyData, setAppState }) => (
    <div className="p-4">
        <h2 className="text-xl font-bold mb-2">Journey Screen</h2>
        <p>Next Stop: {journeyData.endStop}</p>
        <p>Remaining Time: {journeyData.total_journey_min} min</p>
        <button
            className="mt-4 p-2 bg-blue-600 text-white rounded"
            onClick={() => setAppState('USER_PANEL')}
        >
            Back to Home
        </button>
    </div>
);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
