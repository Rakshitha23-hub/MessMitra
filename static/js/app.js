
// ========================================
// MESSMITRA JAVASCRIPT
// ========================================


// ---------- AI FOOD PREDICTOR ----------

async function predictFood() {
    const attendance = document.getElementById("attendance");
    const mealType = document.getElementById("mealType");
    const result = document.getElementById("predictionResult");

    if (!attendance || !mealType || !result) return;

    if (!attendance.value || Number(attendance.value) <= 0) {
        result.innerText = "Please enter valid attendance.";
        return;
    }

    try {
        const response = await fetch("/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: new URLSearchParams({
                attendance: attendance.value,
                meal_type: mealType.value
            })
        });

        const data = await response.json();

        result.innerText = data.recommended
            ? `Recommended portions: ${data.recommended}`
            : data.error || "Prediction unavailable.";

    } catch (error) {
        console.error("Prediction error:", error);
        result.innerText = "Unable to get prediction.";
    }
}


// ---------- MITRA ASSISTANT ----------

async function askMitra() {
    const input = document.getElementById("question");
    const chat = document.getElementById("chat");

    if (!input || !chat) return;

    const message = input.value.trim();

    if (!message) return;

    chat.innerHTML += `<p><strong>You:</strong> ${escapeHTML(message)}</p>`;
    input.value = "";

    try {
        const response = await fetch("/assistant", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        chat.innerHTML += `<p><strong>Mitra:</strong> ${escapeHTML(data.reply || "I couldn't generate a response.")}</p>`;

        chat.scrollTop = chat.scrollHeight;

    } catch (error) {
        console.error("Assistant error:", error);
        chat.innerHTML += "<p><strong>Mitra:</strong> Something went wrong. Please try again.</p>";
    }
}


// Prevent user messages from being interpreted as HTML
function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[character]);
}


// ---------- FOOD IMPACT ANALYTICS ----------

let impactChartInstance = null;
let utilizationChartInstance = null;

async function loadAnalytics() {

    try {
        const response = await fetch("/analytics");

        if (!response.ok) {
            throw new Error("Analytics API returned " + response.status);
        }

        const data = await response.json();

        // Update summary cards
        document.getElementById("totalPrepared").textContent =
            data.total_prepared ?? 0;

        document.getElementById("totalConsumed").textContent =
            data.total_consumed ?? 0;

        document.getElementById("totalWasted").textContent =
            data.total_wasted ?? 0;

        document.getElementById("utilization").textContent =
            (data.utilization ?? 0) + "%";

        // Update Green Mess Score
        const score = Number(data.green_score ?? 0);

        document.getElementById("analyticsScore").textContent = score;

        document.getElementById("scoreProgress").style.width =
            Math.min(100, Math.max(0, score)) + "%";

        // Get chart elements
        const impactCanvas = document.getElementById("impactChart");
        const utilizationCanvas = document.getElementById("utilizationChart");

        if (!impactCanvas || !utilizationCanvas) {
            console.error("Analytics canvas elements not found.");
            return;
        }

        if (typeof Chart === "undefined") {
            throw new Error("Chart.js is not loaded.");
        }

        // Destroy old charts before creating new ones
        if (impactChartInstance) impactChartInstance.destroy();
        if (utilizationChartInstance) utilizationChartInstance.destroy();

        // Daily Food Trends
        impactChartInstance = new Chart(impactCanvas, {
            type: "line",

            data: {
                labels: data.dates || [],

                datasets: [
                    {
                        label: "Prepared",
                        data: data.prepared || [],
                        borderColor: "#16a34a",
                        backgroundColor: "rgba(22,163,74,0.10)",
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: "Consumed",
                        data: data.consumed || [],
                        borderColor: "#2563eb",
                        backgroundColor: "rgba(37,99,235,0.10)",
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: "Wasted",
                        data: data.wasted || [],
                        borderColor: "#ef4444",
                        backgroundColor: "rgba(239,68,68,0.10)",
                        fill: true,
                        tension: 0.4
                    }
                ]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom"
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });


        // Food Utilization Doughnut Chart
        utilizationChartInstance = new Chart(utilizationCanvas, {
            type: "doughnut",

            data: {
                labels: ["Consumed", "Wasted"],

                datasets: [{
                    data: [
                        data.total_consumed ?? 0,
                        data.total_wasted ?? 0
                    ],
                    backgroundColor: [
                        "#16a34a",
                        "#f97316"
                    ],
                    borderWidth: 0
                }]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom"
                    }
                }
            }
        });

        const message = document.getElementById("analyticsMessage");

        if (message) {
            message.textContent = data.total_prepared > 0
                ? "Your food impact analytics are updated successfully."
                : "Add meal records to start viewing your food impact analytics.";
        }

    } catch (error) {
        console.error("Analytics error:", error);

        const message = document.getElementById("analyticsMessage");

        if (message) {
            message.textContent = "Unable to load analytics. Please check your connection and try again.";
        }
    }
}


// ---------- PAGE INITIALIZATION ----------

document.addEventListener("DOMContentLoaded", function () {

    loadAnalytics();

});

// ========================================
// MESSMITRA FOOD IMPACT ANALYTICS
// ========================================

let impactChartInstance = null;
let utilizationChartInstance = null;

async function loadAnalytics() {

    const impactCanvas = document.getElementById("impactChart");
    const utilizationCanvas = document.getElementById("utilizationChart");

    // Check whether analytics elements exist
    if (!impactCanvas || !utilizationCanvas) {
        console.error("Analytics canvas elements not found!");
        return;
    }

    // Check Chart.js
    if (typeof Chart === "undefined") {
        console.error("Chart.js library is not loaded!");
        return;
    }

    try {

        console.log("Loading MessMitra Analytics...");

        // Fetch data from Flask
        const response = await fetch("/analytics");

        if (!response.ok) {
            throw new Error("Analytics API error: " + response.status);
        }

        const result = await response.json();

        console.log("Analytics Data:", result);

        // Support both array and object API formats
        const records = Array.isArray(result)
            ? result
            : (result.records || []);

        const dates = Array.isArray(result)
            ? records.map(item => item.meal_date)
            : (result.dates || []);

        const prepared = Array.isArray(result)
            ? records.map(item => Number(item.prepared) || 0)
            : (result.prepared || []).map(Number);

        const consumed = Array.isArray(result)
            ? records.map(item => Number(item.consumed) || 0)
            : (result.consumed || []).map(Number);

        const wasted = Array.isArray(result)
            ? records.map(item => Number(item.wasted) || 0)
            : (result.wasted || []).map(Number);

        const totalPrepared = Array.isArray(result)
            ? prepared.reduce((a, b) => a + b, 0)
            : Number(result.total_prepared || 0);

        const totalConsumed = Array.isArray(result)
            ? consumed.reduce((a, b) => a + b, 0)
            : Number(result.total_consumed || 0);

        const totalWasted = Array.isArray(result)
            ? wasted.reduce((a, b) => a + b, 0)
            : Number(result.total_wasted || 0);

        // Update summary cards if present
        const updateText = (id, value) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        };

        updateText("totalPrepared", totalPrepared);
        updateText("totalConsumed", totalConsumed);
        updateText("totalWasted", totalWasted);

        const utilization = totalPrepared > 0
            ? (totalConsumed / totalPrepared) * 100
            : 0;

        updateText("utilization", utilization.toFixed(1) + "%");

        // Destroy previous charts before recreating
        if (impactChartInstance) {
            impactChartInstance.destroy();
        }

        if (utilizationChartInstance) {
            utilizationChartInstance.destroy();
        }

        // FOOD IMPACT LINE CHART
        impactChartInstance = new Chart(impactCanvas, {

            type: "line",

            data: {
                labels: dates,

                datasets: [

                    {
                        label: "Prepared Food",
                        data: prepared,
                        borderColor: "#2e9d67",
                        backgroundColor: "rgba(46,157,103,0.12)",
                        fill: true,
                        tension: 0.4
                    },

                    {
                        label: "Consumed Food",
                        data: consumed,
                        borderColor: "#3498db",
                        backgroundColor: "rgba(52,152,219,0.12)",
                        fill: true,
                        tension: 0.4
                    },

                    {
                        label: "Food Waste",
                        data: wasted,
                        borderColor: "#e67e22",
                        backgroundColor: "rgba(230,126,34,0.12)",
                        fill: true,
                        tension: 0.4
                    }

                ]
            },

            options: {

                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        display: true,
                        position: "top"
                    },

                    title: {
                        display: true,
                        text: "Daily Food Preparation and Waste"
                    }
                },

                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: "Quantity"
                        }
                    },

                    x: {
                        title: {
                            display: true,
                            text: "Date"
                        }
                    }
                }
            }
        });

        // FOOD UTILIZATION DOUGHNUT CHART

        const unused = Math.max(0, totalPrepared - totalConsumed);

        utilizationChartInstance = new Chart(utilizationCanvas, {

            type: "doughnut",

            data: {

                labels: [
                    "Consumed Food",
                    "Remaining Food"
                ],

                datasets: [{
                    data: [totalConsumed, unused],

                    backgroundColor: [
                        "#2e9d67",
                        "#f39c12"
                    ],

                    borderWidth: 2
                }]
            },

            options: {

                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        position: "bottom"
                    },

                    title: {
                        display: true,
                        text: "Food Utilization Overview"
                    }
                }
            }
        });

        console.log("MessMitra Analytics Loaded Successfully!");

    }

    catch (error) {

        console.error("Analytics Loading Failed:", error);

    }
}


// Load analytics when dashboard is ready

document.addEventListener("DOMContentLoaded", function () {

    loadAnalytics();

});