# ===============================
# app.py - Food Calorie Estimator + Personalized Diet Planner
# ===============================

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from ultralytics import YOLO
import os, shutil
import cv2
from PIL import Image

# ===============================
# 1️⃣ Load YOLOv8 model
# ===============================
MODEL_PATH = "best.pt"
model = YOLO(MODEL_PATH)
print("✅ YOLOv8 model loaded successfully")

# ===============================
# 2️⃣ Food calories per 100g and nutrients
# ===============================
food_data = {
    "Biryani": {"calories": 170, "protein": 5, "carbs": 28, "fat": 6},
    "Shahi Paneer": {"calories": 300, "protein": 12, "carbs": 8, "fat": 25},
    "Dal": {"calories": 120, "protein": 9, "carbs": 15, "fat": 2},
    "Roti": {"calories": 120, "protein": 3, "carbs": 20, "fat": 2},
    "Rice": {"calories": 130, "protein": 2, "carbs": 28, "fat": 0.5},
    "Jalebi": {"calories": 150, "protein": 1, "carbs": 35, "fat": 0.5}
}

# ===============================
# 3️⃣ Initialize FastAPI
# ===============================
app = FastAPI(title="Professional Food Calorie Estimator & Diet Planner")

if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ===============================
# 4️⃣ HTML + CSS + JS
# ===============================
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Food Calorie Estimator & Diet Planner</title>
<style>
body { font-family:'Segoe UI', Tahoma, Geneva, Verdana,sans-serif; background:#f0f2f5; margin:0; padding:0; }
.container { max-width:900px; margin:40px auto; background:#fff; padding:30px; border-radius:15px; box-shadow:0 4px 20px rgba(0,0,0,0.15);}
h1 { color:#ff6600; text-align:center; }
input[type=file], input[type=number] { display:block; margin:10px 0; padding:8px; width:100%; border-radius:5px; border:1px solid #ccc;}
button { padding:12px 25px; background:#ff6600; color:#fff; border:none; border-radius:6px; cursor:pointer; font-size:16px;}
button:hover { background:#e65c00; }
img { border-radius:12px; margin-top:20px; max-width:100%; border:1px solid #ccc; }
table { width:100%; border-collapse:collapse; margin-top:20px; }
th, td { border:1px solid #ddd; padding:10px; text-align:center; }
th { background:#ff6600; color:#fff; }
tr:nth-child(even) { background:#f9f9f9; }
#dietPlanner { margin-top:30px; padding:15px; border:1px solid #ddd; border-radius:10px; background:#fafafa; }
</style>
</head>
<body>
<div class="container">
<h1>🍽️ Food Calorie Estimator & Diet Planner</h1>
<p>Upload a food image and provide approximate weight (grams) for precise calories.</p>

<form id="uploadForm">
<input type="file" id="fileInput" name="file" required>
<button type="submit">Upload & Predict</button>
</form>

<div id="results" style="display:none;">
<h2>Detected Foods:</h2>
<table id="resultsTable">
<tr>
<th>Food Item</th>
<th>Confidence</th>
<th>Weight (g)</th>
<th>Calories</th>
<th>Protein (g)</th>
<th>Carbs (g)</th>
<th>Fat (g)</th>
</tr>
</table>
<h3>Total Calories: <span id="totalCalories">0</span> kcal</h3>
<img id="outputImage" src="" alt="Detected Image">
</div>

<div id="dietPlanner" style="display:none;">
<h2>📝 Personalized Diet Planner</h2>
<p>Enter your daily target calories:</p>
<input type="number" id="targetCalories" placeholder="e.g., 2000">
<button id="planButton">Generate Diet Plan</button>
<table id="dietTable">
<tr>
<th>Food Item</th>
<th>Recommended Weight (g)</th>
<th>Calories</th>
</tr>
</table>
</div>

<script>
const form = document.getElementById('uploadForm');
form.addEventListener('submit', async (e)=>{
    e.preventDefault();
    const fileInput = document.getElementById('fileInput');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    const res = await fetch('/predict/', { method:'POST', body: formData });
    const data = await res.json();
    if(data.error){ alert("Error: "+data.error); return; }

    document.getElementById('results').style.display='block';
    const table = document.getElementById('resultsTable');
    table.innerHTML = "<tr><th>Food Item</th><th>Confidence</th><th>Weight (g)</th><th>Calories</th><th>Protein (g)</th><th>Carbs (g)</th><th>Fat (g)</th></tr>";

    let totalCalories = 0;
    window.detectedFoods = []; // store for diet planner

    data.items.forEach(item=>{
        let weight = prompt(`Enter approximate weight in grams for ${item.class}:`, "100");
        weight = parseFloat(weight)||100;
        const calories = Math.round(item.calories_per_100g.calories * weight/100);
        const protein = Math.round(item.calories_per_100g.protein * weight/100);
        const carbs = Math.round(item.calories_per_100g.carbs * weight/100);
        const fat = Math.round(item.calories_per_100g.fat * weight/100);

        totalCalories += calories;

        const row = table.insertRow();
        row.insertCell(0).textContent = item.class;
        row.insertCell(1).textContent = (item.confidence*100).toFixed(1)+"%";
        row.insertCell(2).textContent = weight;
        row.insertCell(3).textContent = calories;
        row.insertCell(4).textContent = protein;
        row.insertCell(5).textContent = carbs;
        row.insertCell(6).textContent = fat;

        window.detectedFoods.push({
            class:item.class,
            calories_per_100g:item.calories_per_100g
        });
    });

    document.getElementById('totalCalories').textContent = totalCalories;
    document.getElementById('outputImage').src = data.output_image;
    document.getElementById('dietPlanner').style.display='block';
});

document.getElementById('planButton').addEventListener('click', ()=>{
    const target = parseFloat(document.getElementById('targetCalories').value);
    if(!target){ alert("Enter a valid target calories."); return; }
    const dietTable = document.getElementById('dietTable');
    dietTable.innerHTML = "<tr><th>Food Item</th><th>Recommended Weight (g)</th><th>Calories</th></tr>";

    // simple proportional planner
    const totalDetectedCalories = window.detectedFoods.reduce((sum,f)=>sum+f.calories_per_100g.calories,0);
    window.detectedFoods.forEach(f=>{
        const ratio = f.calories_per_100g.calories/totalDetectedCalories;
        const recommendedCalories = target * ratio;
        const recommendedWeight = Math.round(recommendedCalories / f.calories_per_100g.calories * 100);
        const row = dietTable.insertRow();
        row.insertCell(0).textContent = f.class;
        row.insertCell(1).textContent = recommendedWeight;
        row.insertCell(2).textContent = Math.round(recommendedCalories);
    });
});
</script>
</div>
</body>
</html>
"""

# ===============================
# 5️⃣ Home route
# ===============================
@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(html_content)

# ===============================
# 6️⃣ Predict route
# ===============================
@app.post("/predict/")
async def predict_calories(file: UploadFile = File(...)):
    try:
        file_path = os.path.join("static", f"temp_{file.filename}")
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # YOLOv8 detection
        results = model.predict(source=file_path, conf=0.35, save=False, verbose=False, imgsz=640, device='cpu')
        result = results[0]

        # Load original image
        img = cv2.imread(file_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        items = []
        # Draw orange rectangle boxes
        for box, cls, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
            x1, y1, x2, y2 = map(int, box)
            class_name = result.names[int(cls)]
            cv2.rectangle(img, (x1, y1), (x2, y2), color=(255,165,0), thickness=3)
            cv2.putText(img, class_name, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,165,0), 2)

            items.append({
                "class": class_name,
                "confidence": float(conf),
                "calories_per_100g": food_data.get(class_name, {"calories":0,"protein":0,"carbs":0,"fat":0})
            })

        # Save annotated image
        output_image_path = os.path.join("static", f"pred_{file.filename}")
        Image.fromarray(img).save(output_image_path)

        return JSONResponse({
            "items": items,
            "output_image": f"/{output_image_path.replace(os.sep,'/')}"
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
