
// ---------------- AI FOOD PREDICTOR ----------------

async function predictFood() {
    const attendance = document.getElementById("attendance").value;
    const mealType = document.getElementById("meal_type").value;
    const result = document.getElementById("prediction_result");

    if (!attendance || Number(attendance) <= 0) {
        result.textContent = "Please enter valid attendance.";
        return;
    }

    result.textContent = "Calculating recommended portions...";

    try {
        const response = await fetch("/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: new URLSearchParams({
                attendance: attendance,
                meal_type: mealType
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Prediction failed.");
        }

        result.textContent =
            `🌱 ${mealType}: Prepare approximately ${data.recommended} portions for ${attendance} students.`;

    } catch (error) {
        result.textContent = error.message;
    }
}


// ---------------- MITRA ASSISTANT ----------------

async function askMitra() {
    const input = document.getElementById("question");
    const chat = document.getElementById("chat");

    const message = input.value.trim();

    if (!message) return;

    const userMessage = document.createElement("div");
    userMessage.className = "user-message";
    userMessage.textContent = message;

    chat.appendChild(userMessage);
    input.value = "";

    const loading = document.createElement("div");
    loading.className = "bot-message";
    loading.textContent = "Mitra is thinking...";
    chat.appendChild(loading);

    chat.scrollTop = chat.scrollHeight;

    try {
        const response = await fetch("/assistant", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to get a response.");
        }

        loading.textContent = data.answer || "Sorry, I couldn't understand that.";

    } catch (error) {
        loading.textContent = error.message;
    }

    chat.scrollTop = chat.scrollHeight;
}


// ---------------- FOOD IMPACT ANALYTICS ----------------

async function loadAnalytics() {
    const canvas = document.getElementById("impactChart");

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    try {
        const response = await fetch("/analytics");

        if (!response.ok) {
            throw new Error("Analytics could not be loaded.");
        }

        const data = await response.json();

        if (window.messMitraChart) {
            window.messMitraChart.destroy();
        }

        window.messMitraChart = new Chart(canvas, {
            type: "bar",

            data: {
                labels: data.dates,

                datasets: [
                    {
                        label: "Prepared",
                        data: data.prepared,
                        backgroundColor: "#9ac9aa",
                        borderRadius: 6
                    },
                    {
                        label: "Consumed",
                        data: data.consumed,
                        backgroundColor: "#16834a",
                        borderRadius: 6
                    },
                    {
                        label: "Wasted",
                        data: data.wasted,
                        backgroundColor: "#f2a477",
                        borderRadius: 6
                    }
                ]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        position: "top"
                    }
                },

                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

    } catch (error) {
        console.error("Analytics error:", error);
    }
}


// ---------------- DASHBOARD INITIALIZATION ----------------

document.addEventListener("DOMContentLoaded", function () {
    loadAnalytics();

    const links = document.querySelectorAll(".nav-link");

    links.forEach(link => {
        link.addEventListener("click", function () {
            links.forEach(item => item.classList.remove("active"));
            this.classList.add("active");
        });
    });
});
