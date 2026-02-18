import React, { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Calendar } from "lucide-react";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TourSelect = ({ onTourSelected }) => {
  const [tours, setTours] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  
  // Create tour form
  const [tourName, setTourName] = useState("");
  const [tourCode, setTourCode] = useState("");
  const [startDate, setStartDate] = useState("");
  const [multiTourAccess, setMultiTourAccess] = useState(false);

  useEffect(() => {
    loadTours();
  }, []);

  const loadTours = async () => {
    try {
      const response = await axios.get(`${API}/tours`);
      setTours(response.data);
    } catch (error) {
      console.error("Failed to load tours:", error);
      toast.error("Failed to load tours");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTour = async () => {
    if (!tourName || !startDate) {
      toast.error("Please fill in required fields");
      return;
    }

    try {
      setCreating(true);
      const response = await axios.post(`${API}/tours`, {
        tour_name: tourName,
        tour_code: tourCode || undefined,
        start_date: new Date(startDate).toISOString(),
        multi_tour_access: multiTourAccess
      });
      
      toast.success(`Tour created: ${response.data.tour_code}`);
      onTourSelected(response.data);
    } catch (error) {
      console.error("Failed to create tour:", error);
      toast.error("Failed to create tour");
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen" data-testid="loading-spinner">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading tours...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-12" data-testid="tour-select-screen">
      <Toaster />
      
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2" data-testid="page-title">TourText Admin</h1>
          <p className="text-slate-600" data-testid="page-subtitle">
            Select an existing tour or create a new one.
          </p>
        </div>

        {/* Create New Tour */}
        <Card className="mb-8" data-testid="create-tour-card">
          <CardHeader>
            <CardTitle data-testid="create-tour-title">Create New Tour</CardTitle>
            <CardDescription data-testid="create-tour-description">
              Set up a new tour to start uploading information.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="tour-name" data-testid="tour-name-label">Tour Name *</Label>
                  <Input
                    id="tour-name"
                    placeholder="e.g., Kings of Leon 2026"
                    value={tourName}
                    onChange={(e) => setTourName(e.target.value)}
                    data-testid="tour-name-input"
                  />
                </div>
                
                <div>
                  <Label htmlFor="tour-code" data-testid="tour-code-label">
                    Tour Code (optional)
                  </Label>
                  <Input
                    id="tour-code"
                    placeholder="e.g., KOL26"
                    value={tourCode}
                    onChange={(e) => setTourCode(e.target.value.toUpperCase())}
                    data-testid="tour-code-input"
                  />
                  <p className="text-xs text-slate-500 mt-1">Auto-generated if left blank</p>
                </div>
              </div>

              <div>
                <Label htmlFor="start-date" data-testid="start-date-label">Start Date *</Label>
                <Input
                  id="start-date"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  data-testid="start-date-input"
                />
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="multi-tour"
                  checked={multiTourAccess}
                  onCheckedChange={setMultiTourAccess}
                  data-testid="multi-tour-switch"
                />
                <Label htmlFor="multi-tour" data-testid="multi-tour-label">
                  Enable multi-tour access
                </Label>
              </div>

              <Button
                onClick={handleCreateTour}
                disabled={creating}
                className="w-full md:w-auto"
                data-testid="create-tour-button"
              >
                {creating ? "Creating..." : "Create Tour"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Existing Tours */}
        {tours.length > 0 && (
          <div data-testid="existing-tours-section">
            <h2 className="text-2xl font-bold mb-4" data-testid="existing-tours-title">Existing Tours</h2>
            
            <div className="grid md:grid-cols-2 gap-4">
              {tours.map((tour) => (
                <Card
                  key={tour.id}
                  className="cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => onTourSelected(tour)}
                  data-testid={`tour-card-${tour.tour_code}`}
                >
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between" data-testid={`tour-title-${tour.tour_code}`}>
                      {tour.tour_name}
                      <span className="text-sm font-mono bg-blue-100 text-blue-700 px-2 py-1 rounded" data-testid={`tour-code-badge-${tour.tour_code}`}>
                        {tour.tour_code}
                      </span>
                    </CardTitle>
                    <CardDescription className="flex items-center gap-2" data-testid={`tour-start-date-${tour.tour_code}`}>
                      <Calendar className="h-4 w-4" />
                      {new Date(tour.start_date).toLocaleDateString()}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-slate-600" data-testid={`tour-tid-${tour.tour_code}`}>
                      TID: {tour.tid}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {tours.length === 0 && (
          <div className="text-center py-12 bg-slate-100 rounded-lg" data-testid="no-tours-message">
            <p className="text-slate-600">No existing tours. Create your first tour above.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TourSelect;
