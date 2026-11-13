
// Prediction form
const form = document.getElementById("predictionForm");

form.addEventListener("submit", async function(event) {

    event.preventDefault();

    const resultBox = document.getElementById("predictionResult");

    const formData = new FormData(form);

    const inputData = {};

    formData.forEach((value, key) => {
        inputData[key] = value;
    });

    resultBox.textContent = "Generating prediction...";

    try {

        const response = await fetch("/api/predict", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(inputData)

        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Prediction failed");
        }

        resultBox.textContent =
            "Predicted next-day PM2.5: " +
            data.prediction + " " + data.unit +
            " | Model: " + data.model;

        resultBox.style.background = "#d9f5e9";

        // Refresh dashboard after prediction
        loadDashboard();

    }

    catch(error) {

        resultBox.textContent = "Error: " + error.message;

        resultBox.style.background = "#ffe1e1";

    }

});


// Load dashboard information
async function loadDashboard() {

    try {

        const response = await fetch("/api/dashboard");

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Dashboard loading failed");
        }

        document.getElementById("totalPredictions").textContent =
            data.total_predictions;

        document.getElementById("bestModel").textContent =
            data.best_model;

        // Display model comparison
        const modelTable = document.getElementById("modelTable");

        modelTable.replaceChildren();

        data.model_results.forEach(model => {

            const row = document.createElement("tr");

            [
                model.Model,
                model.MAE,
                model.MSE,
                model.RMSE,
                model["R2 Score"]
            ].forEach(value => {

                const cell = document.createElement("td");

                cell.textContent =
                    typeof value === "number"
                    ? value.toFixed(4)
                    : value;

                row.appendChild(cell);

            });

            modelTable.appendChild(row);

        });


        // Display prediction history
        const historyTable =
            document.getElementById("historyTable");

        historyTable.replaceChildren();

        data.history.forEach(item => {

            const row = document.createElement("tr");

            [
                item.id,
                item.prediction_date,
                item.pm25_prediction,
                item.model_name
            ].forEach(value => {

                const cell = document.createElement("td");

                cell.textContent = value;

                row.appendChild(cell);

            });

            historyTable.appendChild(row);

        });

    }

    catch(error) {

        console.error("Dashboard error:", error);

    }

}


// Load dashboard when website opens
loadDashboard();
