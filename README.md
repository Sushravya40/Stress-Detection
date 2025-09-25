# Stress Detection in IT Professionals using Machine Learning

![Python](https://img.shields.io/badge/Python-3.11-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

This project focuses on detecting stress levels in IT professionals using machine learning techniques.  
It uses data preprocessing, feature extraction, and classification models to predict stress levels.

---

## 🚀 Features
- Data cleaning and preprocessing
- Feature extraction from datasets
- Machine learning model training (e.g., SVM, Random Forest, Neural Networks)
- Model evaluation with accuracy, precision, recall, F1-score
- Visualization of results

---

## 🛠️ Tech Stack
- Python (pandas, numpy, scikit-learn, matplotlib, seaborn)
- Flask / Streamlit (optional for deployment)
- MySQL / SQLite (optional database)

---

## 📂 Project Structure
stress-detection/
│-- data/ # Dataset files
│-- models/ # Trained ML models
│-- notebooks/ # Jupyter notebooks for analysis
│-- app.py # Main application / deployment file
│-- requirements.txt # Python dependencies
│-- README.md # Project documentation


## 📂 Dataset
The dataset used in this project is from Kaggle:  
[Stress Detection in IT Professionals Dataset](https://www.kaggle.com/datasets/csepython/stress-detection-it-professionals-dataset)

**How to Use It:**
1. Download the dataset from Kaggle (you’ll need a Kaggle account).  
2. Place the CSV/data files inside the `data/` folder.  
3. Load the dataset in your code:
   ```python
   import pandas as pd
   df = pd.read_csv("data/your_dataset_file.csv")
▶️ How to Run
1 Clone the repository:
git clone https://github.com/Sushravya40/stress-detection.git
cd stress-detection

2 Install dependencies:
pip install -r requirements.txt

3 Run the application:
python app.py


📊 Results
Model accuracy achieved: 96%

Best performing algorithm: Random Forest

Visualizations and plots available in notebooks/ folder

📌 Future Scope
Real-time stress detection
Mobile / Cloud deployment
Integration with wearable devices
Advanced feature engineering and deep learning models

👨‍💻 Author
Sushravya
GitHub: Sushravya40

📜 License
This project is licensed under the MIT License.

This README now has:  
- Badges (Python, License, Status)  
- Dataset section with link  
- Clear project structure  
- Usage instructions  
- Future scope & author info  
