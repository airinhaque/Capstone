# Neck-Wearable Cuffless Blood Pressure Monitor

##  Project Goal
We are building a **neck-wearable device** that can measure blood pressure **without using the traditional cuff**.  
Instead, we use **PPG (photoplethysmography) sensors** to calculate **Pulse Transit Time (PTT)**  the time it takes for a pulse wave to travel between two points.  

Other wearables like Apple Watch or WHOOP try to do this, but they are not FDA approved and not accurate enough.  
Our target is to meet the **AAMI medical standard** (≤ **5 mmHg error**).



## 🫀 Why the Neck?
- The **carotid arteries** in the neck give stronger and more reliable signals than the wrist.  
- This makes our device more accurate than watches or wristbands.  
- Comfortable to wear and works for continuous monitoring.  



## ⚙️ System Overview

**Step 1  Sensors**
- Start with **1 PPG sensor** (test signals).  
- Add **2 sensors** to measure PTT.  
- Extend to **4 PPG sensors** around the neck for better accuracy.  
- Future: add **temperature, accelerometer, and gyroscope**.

**Step 2  Signal Processing**
- Collect PPG signals.  
- Filter and clean the data.  
- Extract key features: pulse width, peak intervals, transit delay.  

**Step 3 Data Transfer**
- Send processed data via **Bluetooth Low Energy (BLE)** to a laptop or phone.  

**Step 4  Machine Learning**
- Train a model to predict blood pressure using extracted features.  
- Improve accuracy with more data (students + patient trials).  

**Step 5 Visualization**
- Build an **app/dashboard** to show:  
  - Blood pressure trends  
  - Heart rate & PPG waveforms  
  - Motion/temperature (future)



## 🧪 Testing Plan
- Compare against standard cuff devices.  
- Must achieve **≤ 5 mmHg error (AAMI standard)**.  
- Start with students → extend to patients.  
- Test during normal daily movement.  


