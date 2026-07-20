// Application State
let laptops = [];
let filteredLaptops = [];
let stats = {};
let currentPage = 1;
const itemsPerPage = 12;

// Chart.js Instances (saved to destroy before redraw)
let brandChart = null;
let processorChart = null;

// DOM Elements
document.addEventListener("DOMContentLoaded", () => {
    // Load saved settings
    loadSettings();

    // Fetch database stats & laptop list
    fetchStats();
    fetchCatalog();
});

// Toast Notification Helper
function showToast(message, type = 'info') {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    toast.innerHTML = `
        <span>${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;

    container.appendChild(toast);

    // Auto remove after 4 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Collapsible Card System
function toggleCard(cardId) {
    const card = document.getElementById(cardId);
    card.classList.toggle("collapsed");
    const icon = card.querySelector(".collapse-icon");
    if (card.classList.contains("collapsed")) {
        icon.innerText = "▼";
    } else {
        icon.innerText = "▲";
    }
}

// Manage Settings in LocalStorage
function loadSettings() {
    const provider = localStorage.getItem("llm_provider") || "gemini";
    const apiKey = localStorage.getItem("llm_api_key") || "";

    document.getElementById("provider-select").value = provider;
    document.getElementById("api-key-input").value = apiKey;

    onProviderChange();
}

function saveSettings() {
    const provider = document.getElementById("provider-select").value;
    const apiKey = document.getElementById("api-key-input").value.strip();

    localStorage.setItem("llm_provider", provider);
    localStorage.setItem("llm_api_key", apiKey);
}

// String polyfill for trim/strip
if (!String.prototype.strip) {
    String.prototype.strip = function () {
        return this.trim();
    };
}

function onProviderChange() {
    const provider = document.getElementById("provider-select").value;
    const apiKeyLabel = document.getElementById("api-key-label");
    const apiKeyInput = document.getElementById("api-key-input");

    if (provider === "gemini") {
        apiKeyLabel.innerText = "Gemini API Key";
        apiKeyInput.placeholder = "AIzaSy...";
    } else if (provider === "openai") {
        apiKeyLabel.innerText = "OpenAI API Key";
        apiKeyInput.placeholder = "sk-proj-...";
    } else if (provider === "kimi") {
        apiKeyLabel.innerText = "NVIDIA API Key";
        apiKeyInput.placeholder = "nvapi-...";
    }
}

// Budget Slider Value
function updateBudgetValue(value) {
    document.getElementById("budget-value").innerText = Number(value).toLocaleString() + " INR";
}

// Tab Switching Control
function switchTab(tabId) {
    // Toggle active buttons
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.classList.remove("active");
    });

    // Set active button
    event.currentTarget.classList.add("active");

    // Toggle active sections
    document.querySelectorAll(".tab-content").forEach(content => {
        content.classList.remove("active");
    });

    document.getElementById(tabId).classList.add("active");
}

// Fetch Catalog Data from Server
async function fetchCatalog() {
    try {
        const response = await fetch("/api/laptops");
        if (!response.ok) throw new Error("Could not fetch laptops");
        laptops = await response.json();
        filteredLaptops = [...laptops];

        // Populate filter dropdown choices
        populateFilters();

        // Render Catalog Grid
        renderCatalog();
    } catch (err) {
        showToast("Error loading laptop catalog: " + err.message, "error");
    }
}

// Populate Catalog Dropdown Filters Dynamically
function populateFilters() {
    const brands = new Set();
    const processors = new Set();

    laptops.forEach(laptop => {
        if (laptop.Brand) brands.add(laptop.Brand);
        if (laptop.Processor) processors.add(laptop.Processor);
    });

    const brandSelect = document.getElementById("filter-brand");
    const procSelect = document.getElementById("filter-processor");

    // Reset but keep first 'All' option
    brandSelect.innerHTML = '<option value="All">All Brands</option>';
    procSelect.innerHTML = '<option value="All">All CPUs</option>';

    Array.from(brands).sort().forEach(b => {
        brandSelect.innerHTML += `<option value="${b}">${b}</option>`;
    });

    Array.from(processors).sort().forEach(p => {
        procSelect.innerHTML += `<option value="${p}">${p}</option>`;
    });
}

// Client Side Filter Catalog Grid
function filterCatalog() {
    const searchVal = document.getElementById("catalog-search").value.toLowerCase();
    const brandVal = document.getElementById("filter-brand").value;
    const ramVal = document.getElementById("filter-ram").value;
    const procVal = document.getElementById("filter-processor").value;
    const sortVal = document.getElementById("filter-sort").value;

    filteredLaptops = laptops.filter(laptop => {
        // Search text check
        const textMatch = !searchVal ||
            laptop.Brand.toLowerCase().includes(searchVal) ||
            laptop.Processor.toLowerCase().includes(searchVal) ||
            laptop.OS.toLowerCase().includes(searchVal) ||
            (laptop.Color && laptop.Color.toLowerCase().includes(searchVal));

        // Brand check
        const brandMatch = brandVal === "All" || laptop.Brand === brandVal;

        // RAM check
        const ramMatch = ramVal === "All" || laptop.RAM >= parseInt(ramVal);

        // Processor check
        const procMatch = procVal === "All" || laptop.Processor === procVal;

        return textMatch && brandMatch && ramMatch && procMatch;
    });

    // Sorting
    if (sortVal === "price-asc") {
        filteredLaptops.sort((a, b) => a.Price - b.Price);
    } else if (sortVal === "price-desc") {
        filteredLaptops.sort((a, b) => b.Price - a.Price);
    } else if (sortVal === "rating-desc") {
        filteredLaptops.sort((a, b) => b.Rating - a.Rating);
    }

    currentPage = 1;
    renderCatalog();
}

// Render Laptops in Grid
function renderCatalog() {
    const grid = document.getElementById("catalog-grid");
    const emptyState = document.getElementById("catalog-empty");
    grid.innerHTML = "";

    if (filteredLaptops.length === 0) {
        emptyState.classList.remove("hidden");
        document.getElementById("catalog-pagination").innerHTML = "";
        return;
    }

    emptyState.classList.add("hidden");

    // Pagination Index
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, filteredLaptops.length);
    const paginatedItems = filteredLaptops.slice(startIndex, endIndex);

    paginatedItems.forEach(laptop => {
        const card = document.createElement("div");
        card.className = "laptop-card";

        card.innerHTML = `
            <div class="card-top">
                <span class="laptop-brand">${laptop.Brand}</span>
                <span class="laptop-rating">
                    <svg class="star-icon" viewBox="0 0 24 24" width="14" height="14">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                    </svg>
                    ${Number(laptop.Rating).toFixed(1)}
                </span>
            </div>
            <h4 class="laptop-title">${laptop.Brand} Laptop (${laptop.Processor} Core)</h4>
            <div class="specs-grid">
                <div class="spec-item">
                    <span class="spec-lbl">RAM</span>
                    <span class="spec-val">${laptop.RAM} GB</span>
                </div>
                <div class="spec-item">
                    <span class="spec-lbl">Storage</span>
                    <span class="spec-val">${laptop.SSD_Storage} GB SSD</span>
                </div>
                <div class="spec-item">
                    <span class="spec-lbl">Processor</span>
                    <span class="spec-val">${laptop.Processor}</span>
                </div>
                <div class="spec-item">
                    <span class="spec-lbl">OS</span>
                    <span class="spec-val">${laptop.OS}</span>
                </div>
            </div>
            <div class="card-bottom">
                <span class="laptop-price"><span class="currency-sym">₹</span>${Number(laptop.Price).toLocaleString()}</span>
                <span class="laptop-color-badge">${laptop.Color || 'Unknown'}</span>
            </div>
        `;

        grid.appendChild(card);
    });

    renderPagination();
}

// Render Pagination controls
function renderPagination() {
    const container = document.getElementById("catalog-pagination");
    container.innerHTML = "";

    const totalPages = Math.ceil(filteredLaptops.length / itemsPerPage);
    if (totalPages <= 1) return;

    // Prev button
    const prevBtn = document.createElement("button");
    prevBtn.className = `page-btn ${currentPage === 1 ? 'disabled' : ''}`;
    prevBtn.innerHTML = "&lt;";
    prevBtn.onclick = () => {
        if (currentPage > 1) {
            currentPage--;
            renderCatalog();
        }
    };
    container.appendChild(prevBtn);

    // Page Numbers (Show max 5 pages around current page)
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
    }

    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement("button");
        pageBtn.className = `page-btn ${currentPage === i ? 'active' : ''}`;
        pageBtn.innerText = i;
        pageBtn.onclick = () => {
            currentPage = i;
            renderCatalog();
        };
        container.appendChild(pageBtn);
    }

    // Next button
    const nextBtn = document.createElement("button");
    nextBtn.className = `page-btn ${currentPage === totalPages ? 'disabled' : ''}`;
    nextBtn.innerHTML = "&gt;";
    nextBtn.onclick = () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderCatalog();
        }
    };
    container.appendChild(nextBtn);
}

// Fetch Database Stats from Server
async function fetchStats() {
    try {
        const response = await fetch("/api/stats");
        if (!response.ok) throw new Error("Could not fetch database statistics");
        stats = await response.json();

        // Update elements
        document.getElementById("header-stats-badge").innerText = `${stats.total_records} Laptops Loaded`;
        document.getElementById("stat-total").innerText = stats.total_records.toLocaleString();
        document.getElementById("stat-avg-price").innerText = "₹" + Math.round(stats.avg_price).toLocaleString();
        document.getElementById("stat-avg-rating").innerText = stats.avg_rating.toFixed(2) + " / 5.0";
        document.getElementById("stat-price-range").innerText = `₹${stats.min_price.toLocaleString()} - ₹${stats.max_price.toLocaleString()}`;

        // Draw charts in Analytics Tab
        renderCharts(stats);
    } catch (err) {
        document.getElementById("header-stats-badge").innerText = "Database error";
        showToast("Error retrieving stats: " + err.message, "error");
    }
}

// Render Interactive Analytics Charts using Chart.js
function renderCharts(data) {
    // Destroy previous charts if redraw
    if (brandChart) brandChart.destroy();
    if (processorChart) processorChart.destroy();

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: '#e5e7eb',
                    font: { family: 'Inter', size: 11 }
                }
            }
        },
        scales: {
            y: {
                grid: { color: 'rgba(255, 255, 255, 0.08)' },
                ticks: { color: '#9ca3af', font: { family: 'Inter' } }
            },
            x: {
                grid: { display: false },
                ticks: { color: '#9ca3af', font: { family: 'Inter' } }
            }
        }
    };

    // 1. Brand Chart (Bar Chart)
    const brandCtx = document.getElementById("brand-chart").getContext("2d");
    const brandLabels = Object.keys(data.brands);
    const brandValues = Object.values(data.brands);

    brandChart = new Chart(brandCtx, {
        type: 'bar',
        data: {
            labels: brandLabels,
            datasets: [{
                label: 'Quantity of Laptops',
                data: brandValues,
                backgroundColor: 'rgba(168, 85, 247, 0.65)',
                borderColor: '#a855f7',
                borderWidth: 1.5,
                borderRadius: 6
            }]
        },
        options: chartOptions
    });

    // 2. Processor Chart (Pie/Doughnut Chart)
    const procCtx = document.getElementById("processor-chart").getContext("2d");
    const procLabels = Object.keys(data.processors);
    const procValues = Object.values(data.processors);

    processorChart = new Chart(procCtx, {
        type: 'doughnut',
        data: {
            labels: procLabels,
            datasets: [{
                data: procValues,
                backgroundColor: [
                    'rgba(99, 102, 241, 0.7)',
                    'rgba(236, 72, 153, 0.7)',
                    'rgba(16, 185, 129, 0.7)',
                    'rgba(245, 158, 11, 0.7)',
                    'rgba(59, 130, 246, 0.7)',
                    'rgba(107, 114, 128, 0.7)'
                ],
                borderColor: '#12151b',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#e5e7eb',
                        font: { family: 'Inter', size: 11 }
                    }
                }
            }
        }
    });
}

// Stepper animation controller
let stepTimer = null;
function runTimelineAnimation() {
    // Reset steps
    document.querySelectorAll(".step").forEach(step => {
        step.className = "step";
    });

    const step1 = document.getElementById("step-1");
    const step2 = document.getElementById("step-2");
    const step3 = document.getElementById("step-3");
    const step4 = document.getElementById("step-4");

    step1.classList.add("active");

    let timerCount = 0;

    stepTimer = setInterval(() => {
        timerCount += 1;
        if (timerCount === 3) {
            step1.className = "step completed";
            step2.className = "step active";
        } else if (timerCount === 8) {
            step2.className = "step completed";
            step3.className = "step active";
        } else if (timerCount === 14) {
            step3.className = "step completed";
            step4.className = "step active";
        }
    }, 1000);
}

function stopTimelineAnimation(success = true) {
    if (stepTimer) clearInterval(stepTimer);

    if (success) {
        document.querySelectorAll(".step").forEach(step => {
            step.className = "step completed";
        });
    }
}

// Reset recommendation state
function resetRecommendation() {
    document.getElementById("recommend-results").classList.add("hidden");
    document.getElementById("recommend-empty").classList.remove("hidden");
}

// Submit Recommendation Request to Server
async function submitRecommendation(event) {
    event.preventDefault();

    // Save settings before submitting
    const provider = document.getElementById("provider-select").value;
    const apiKey = document.getElementById("api-key-input").value.strip();

    localStorage.setItem("llm_provider", provider);
    localStorage.setItem("llm_api_key", apiKey);

    // Validate key for all providers; the backend also requires a real key.
    if (!apiKey) {
        showToast("Please enter a valid LLM API Key for the selected provider.", "error");
        // Scroll sidebar to settings if settings closed
        const settingsCard = document.getElementById("settings-card");
        if (settingsCard.classList.contains("collapsed")) {
            toggleCard("settings-card");
        }
        document.getElementById("api-key-input").focus();
        return;
    }

    // Switch to Chat Recommender tab if not active
    switchTab("recommend-tab");

    // UI State Loading
    const emptyState = document.getElementById("recommend-empty");
    const loadingState = document.getElementById("recommend-loading");
    const resultsState = document.getElementById("recommend-results");
    const submitBtn = document.getElementById("submit-btn");
    const btnText = submitBtn.querySelector(".btn-text");
    const btnLoader = submitBtn.querySelector(".btn-loader");

    emptyState.classList.add("hidden");
    resultsState.classList.add("hidden");
    loadingState.classList.remove("hidden");

    submitBtn.disabled = true;
    btnText.style.opacity = '0.5';
    btnLoader.classList.remove("hidden");

    // Start step animation
    runTimelineAnimation();

    // Parse form inputs
    const major = document.getElementById("major-input").value;
    const budget = parseFloat(document.getElementById("budget-range").value);
    const ram = document.getElementById("ram-select").value;
    const os = document.getElementById("os-select").value;
    const brand = document.getElementById("brand-select").value;
    const details = document.getElementById("details-input").value;

    const requestBody = {
        provider: provider,
        major: major,
        budget: budget,
        ram: ram === "Any" ? null : parseFloat(ram),
        brand: brand === "Any" ? null : brand,
        os_name: os === "Any" ? null : os,
        details: details
    };

    try {
        const response = await fetch("/api/recommend", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "x-api-key": apiKey
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Server error running recommendation.");
        }

        const data = await response.json();

        // Stop animation
        stopTimelineAnimation(true);

        // Load date
        const timeNow = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        document.getElementById("recommend-time").innerText = timeNow;

        // Parse markdown using marked.js
        const htmlContent = marked.parse(data.recommendation);
        document.getElementById("recommend-markdown-output").innerHTML = htmlContent;

        // Switch view
        loadingState.classList.add("hidden");
        resultsState.classList.remove("hidden");

        showToast("Recommendation generated successfully!", "success");
    } catch (err) {
        stopTimelineAnimation(false);
        loadingState.classList.add("hidden");
        emptyState.classList.remove("hidden");
        showToast(err.message, "error");
    } finally {
        submitBtn.disabled = false;
        btnText.style.opacity = '1';
        btnLoader.classList.add("hidden");
    }
}

// Trigger Dataset Cleaning Pipeline
async function triggerDataCleaning() {
    const btn = document.getElementById("clean-db-btn");
    const btnText = btn.querySelector(".btn-text");
    const btnLoader = btn.querySelector(".btn-loader");
    const successBadge = document.getElementById("cleaning-success-badge");

    btn.disabled = true;
    btnText.style.opacity = '0.5';
    btnLoader.classList.remove("hidden");
    successBadge.classList.add("hidden");

    try {
        const response = await fetch("/api/clean", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Error cleaning database.");
        }

        const data = await response.json();

        // Success Badge & Toast
        successBadge.classList.remove("hidden");
        showToast(`Cleaning completed: ${data.clean_count} records preserved.`, "success");

        // Reload Stats & Catalog list
        await fetchStats();
        await fetchCatalog();
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        btn.disabled = false;
        btnText.style.opacity = '1';
        btnLoader.classList.add("hidden");
    }
}
