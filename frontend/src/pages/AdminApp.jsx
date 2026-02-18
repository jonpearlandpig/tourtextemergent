import React, { useState, useEffect } from "react";
import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import axios from "axios";

// Admin screens
import TourSelect from "@/pages/admin/TourSelect";
import Upload from "@/pages/admin/Upload";
import LiveStatus from "@/pages/admin/LiveStatus";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminApp = () => {
  const [currentTour, setCurrentTour] = useState(null);
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-50" data-testid="admin-app">
      <Routes>
        <Route
          path="/"
          element={
            <TourSelect
              onTourSelected={(tour) => {
                setCurrentTour(tour);
                navigate("/admin/upload");
              }}
            />
          }
        />
        
        <Route
          path="/upload"
          element={
            currentTour ? (
              <Upload
                tour={currentTour}
                onComplete={() => navigate("/admin/live")}
              />
            ) : (
              <Navigate to="/admin" replace />
            )
          }
        />
        
        <Route
          path="/live"
          element={
            currentTour ? (
              <LiveStatus tour={currentTour} />
            ) : (
              <Navigate to="/admin" replace />
            )
          }
        />
        
        <Route path="*" element={<Navigate to="/admin" replace />} />
      </Routes>
    </div>
  );
};

export default AdminApp;
