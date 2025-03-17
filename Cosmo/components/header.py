"""
Header component for the Gravity app
"""
import streamlit as st

def render_header():
    """Render the Gravity header with branding and animation"""
    # Add custom CSS for the header
    st.markdown("""
    <style>
        /* Gravity Branding Header Styles */
        .Gravity-header {
            display: flex;
            align-items: center;
            padding: 30px;
            background: #000000;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            margin-bottom: 30px;
            position: relative;
            overflow: hidden;
            width: 100%;
            height: 160px;
        }
        
        .stars {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            width: 100%;
            height: 100%;
            background-image: 
                radial-gradient(2px 2px at 20px 30px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0)),
                radial-gradient(2px 2px at 40px 70px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0)),
                radial-gradient(2px 2px at 50px 160px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0)),
                radial-gradient(2px 2px at 90px 40px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0)),
                radial-gradient(2px 2px at 130px 80px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0)),
                radial-gradient(2px 2px at 160px 120px, rgba(255, 255, 255, 0.9), rgba(0, 0, 0, 0));
        }
        
        .Gravity-icon {
            position: relative;
            width: 60px;
            height: 60px;
            margin-right: 20px;
        }
        
        .icon-circle {
            position: absolute;
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: linear-gradient(135deg, #ffeb3b 0%, #ffc107 100%);
            box-shadow: 0 0 20px rgba(255, 235, 59, 0.6);
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .icon-silhouette {
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            width: 30px;
            height: 40px;
        }
        
        .Gravity-title {
            font-family: 'Segoe UI', Arial, sans-serif;
            position: relative;
            z-index: 2;
        }
        
        .brand-name {
            color: #ffffff !important;
            font-size: 48px;
            font-weight: 700;
            letter-spacing: 3px;
            margin: 0;
            text-shadow: 0 2px 8px rgba(255, 255, 255, 0.3);
        }
                
        .Gravity-brand {
            color: #ffffff !important;
            font-weight: 700;
        }
        
        .tagline {
            color: #ffffff;
            font-size: 18px;
            font-weight: 400;
            margin: 5px 0 0 0;
            letter-spacing: 1px;
        }
        
        /* Light beam effect */
        .light-beam {
            position: absolute;
            width: 150px;
            height: 100%;
            background: linear-gradient(90deg, 
                                      rgba(255, 255, 255, 0) 0%, 
                                      rgba(255, 255, 255, 0.1) 50%, 
                                      rgba(255, 255, 255, 0) 100%);
            transform: skewX(-20deg);
            animation: beam 8s infinite;
            opacity: 0.7;
        }
        
        @keyframes beam {
            0% { left: -150px; }
            30% { left: 100%; }
            100% { left: 100%; }
        }
        
        /* Spaceman styling */
        .spaceman {
            position: absolute;
            height: 80px;
            z-index: 2;
            opacity: 0.9;
            /* Combine multiple animations with slower timing */
            animation: 
                drift-x 40s linear infinite alternate, 
                drift-y 35s ease-in-out infinite alternate,
                spin 60s linear infinite;
            /* Start the spaceman in the middle-right area */
            top: 40px;
            right: 100px;
        }
        
        /* Horizontal drifting across the banner */
        @keyframes drift-x {
            0% { right: 30%; }
            20% { right: 80%; }
            40% { right: 20%; }
            60% { right: 65%; }
            80% { right: 40%; }
            100% { right: 70%; }
        }
        
        /* Vertical drifting */
        @keyframes drift-y {
            0% { top: 20px; }
            15% { top: 70px; }
            30% { top: 40px; }
            45% { top: 90px; }
            60% { top: 30px; }
            75% { top: 60px; }
            100% { top: 50px; }
        }
        
        /* Full rotation, including upside down */
        @keyframes spin {
            0% { transform: rotate(0deg); }
            20% { transform: rotate(180deg); }
            40% { transform: rotate(90deg); }
            60% { transform: rotate(360deg); }
            80% { transform: rotate(270deg); }
            100% { transform: rotate(720deg); }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Render the header HTML
    st.markdown("""
    <div class="Gravity-header">
      <div class="stars"></div>
      <div class="light-beam"></div>
      
      <!-- Simple spaceman icon -->
      <div class="spaceman">
        <svg width="100" height="120" viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">
          <!-- Helmet -->
          <circle cx="50" cy="20" r="15" fill="white" opacity="0.9"/>
          <!-- Visor -->
          <circle cx="50" cy="20" r="10" fill="#0088ff" opacity="0.7"/>
          <!-- Body -->
          <rect x="35" y="30" width="30" height="45" rx="8" fill="white" opacity="0.8"/>
          <!-- Arms -->
          <rect x="20" y="40" width="20" height="8" rx="4" fill="white" opacity="0.8"/>
          <rect x="60" y="40" width="20" height="8" rx="4" fill="white" opacity="0.8"/>
          <!-- Legs -->
          <rect x="38" y="75" width="10" height="20" rx="4" fill="white" opacity="0.8"/>
          <rect x="52" y="75" width="10" height="20" rx="4" fill="white" opacity="0.8"/>
        </svg>
      </div>
      
      <div class="Gravity-icon">
        <div class="icon-circle">
          <svg class="icon-silhouette" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L9 9H3L8 14L6 21L12 17L18 21L16 14L21 9H15L12 2Z" fill="white"/>
          </svg>
        </div>
      </div>
      
      <div class="Gravity-title">
        <h1 class="brand-name">Gravity</h1>
        <p class="tagline">To the Stars We Reach, With the News We Lead</p>
      </div>
    </div>
    """, unsafe_allow_html=True)