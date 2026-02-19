import React, { useState, useCallback } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Upload as UploadIcon, FileText, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";
import { useNavigate } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const FILE_TYPES = [
  { value: "mastertour", label: "Master Tour Export", description: "Primary tour data source" },
  { value: "eventbrite", label: "Eventbrite Export", description: "VIP and ticketing data" },
  { value: "onesheet", label: "One Sheet (PDF)", description: "Tour overview" },
  { value: "routing", label: "Routing Sheet", description: "Travel and logistics" },
  { value: "settlement", label: "Settlement", description: "Financial data" },
  { value: "techpack", label: "Tech Pack", description: "Venue technical specs" },
  { value: "other", label: "Other", description: "Miscellaneous files" }
];

const Upload = ({ tour, onComplete }) => {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const navigate = useNavigate();

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFiles(Array.from(e.dataTransfer.files));
    }
  }, [tour]);

  const handleFileInput = async (e) => {
    if (e.target.files && e.target.files[0]) {
      await handleFiles(Array.from(e.target.files));
    }
  };

  const handleFiles = async (files) => {
    setUploading(true);
    
    for (const file of files) {
      try {
        // Detect file type based on filename or let user select
        let fileType = "other";
        const fileName = file.name.toLowerCase();
        
        if (fileName.includes("master") || fileName.includes("tour")) {
          fileType = "mastertour";
        } else if (fileName.includes("eventbrite")) {
          fileType = "eventbrite";
        } else if (fileName.includes("settlement")) {
          fileType = "settlement";
        } else if (fileName.includes("routing")) {
          fileType = "routing";
        } else if (fileName.includes("tech")) {
          fileType = "techpack";
        }

        const formData = new FormData();
        formData.append("file", file);
        formData.append("file_type", fileType);

        const response = await axios.post(
          `${API}/tours/${tour.id}/upload`,
          formData,
          {
            headers: {
              "Content-Type": "multipart/form-data"
            }
          }
        );

        setUploadedFiles(prev => [...prev, response.data]);
        toast.success(`Uploaded: ${file.name}`);
      } catch (error) {
        console.error("Upload failed:", error);
        toast.error(`Failed to upload: ${file.name}`);
      }
    }
    
    setUploading(false);
  };

  const detectCategory = (file) => {
    if (file.file_type === "mastertour") return "Shows & Venues";
    if (file.file_type === "eventbrite") return "VIP & Ticketing";
    if (file.file_type === "settlement") return "Finance";
    if (file.file_type === "routing") return "Travel";
    if (file.file_type === "techpack") return "Technical";
    return "Other";
  };

  const handleActivate = () => {
    if (uploadedFiles.length === 0) {
      toast.error("Please upload at least one file before activating");
      return;
    }
    toast.success("Tour activated!");
    onComplete();
  };

  const handleReprocessAll = async () => {
    try {
      const response = await axios.post(`${API}/tours/${tour.id}/reprocess-all`);
      toast.success(`Reprocessing ${response.data.count} files. This may take a moment...`);
      setTimeout(() => {
        window.location.reload();
      }, 3000);
    } catch (error) {
      console.error("Reprocess failed:", error);
      toast.error("Failed to reprocess files");
    }
  };

  return (
    <div className="container mx-auto px-4 py-12" data-testid="upload-screen">
      <Toaster />
      
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-4xl font-bold" data-testid="page-title">Upload Sources</h1>
            <span className="text-sm font-mono bg-blue-100 text-blue-700 px-3 py-1 rounded" data-testid="tour-code-badge">
              {tour.tour_code}
            </span>
          </div>
          <p className="text-slate-600" data-testid="page-subtitle">
            Upload Master Tour exports, Eventbrite data, PDFs, and other tour sources.
          </p>
        </div>

        {/* Drag & Drop Zone */}
        <Card className="mb-8" data-testid="upload-zone-card">
          <CardContent className="p-0">
            <div
              className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                dragActive
                  ? "border-blue-500 bg-blue-50"
                  : "border-slate-300 hover:border-slate-400"
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              data-testid="drag-drop-zone"
            >
              <div className="flex flex-col items-center gap-4">
                <div className="bg-blue-100 p-4 rounded-full">
                  <UploadIcon className="h-12 w-12 text-blue-600" />
                </div>
                
                <div>
                  <h3 className="text-xl font-semibold mb-2" data-testid="upload-title">
                    Drag and drop files here
                  </h3>
                  <p className="text-slate-600 mb-4" data-testid="upload-subtitle">
                    Supported: CSV, Excel, PDF, ZIP
                  </p>
                </div>

                <div className="flex gap-4">
                  <label htmlFor="file-upload">
                    <Button
                      variant="outline"
                      disabled={uploading}
                      onClick={() => document.getElementById("file-upload").click()}
                      data-testid="browse-files-button"
                    >
                      {uploading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Uploading...
                        </>
                      ) : (
                        "Browse Files"
                      )}
                    </Button>
                  </label>
                  <input
                    id="file-upload"
                    type="file"
                    multiple
                    onChange={handleFileInput}
                    className="hidden"
                    data-testid="file-input"
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Uploaded Files Summary */}
        {uploadedFiles.length > 0 && (
          <Card className="mb-8" data-testid="uploaded-files-card">
            <CardHeader>
              <CardTitle data-testid="uploaded-files-title">Uploaded Files ({uploadedFiles.length})</CardTitle>
              <CardDescription data-testid="uploaded-files-description">
                System auto-detected categories. Files are being processed.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {uploadedFiles.map((file, index) => (
                  <div
                    key={file.id}
                    className="flex items-center justify-between p-4 bg-slate-50 rounded-lg"
                    data-testid={`uploaded-file-${index}`}
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-slate-600" />
                      <div>
                        <p className="font-medium" data-testid={`file-name-${index}`}>{file.file_name}</p>
                        <p className="text-sm text-slate-600" data-testid={`file-category-${index}`}>
                          {detectCategory(file)} • {file.taid}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {file.processed ? (
                        <CheckCircle className="h-5 w-5 text-green-600" data-testid={`file-processed-${index}`} />
                      ) : (
                        <Loader2 className="h-5 w-5 text-blue-600 animate-spin" data-testid={`file-processing-${index}`} />
                      )}
                      <span className="text-sm text-slate-600" data-testid={`file-status-${index}`}>
                        {file.processed ? "Processed" : "Processing..."}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Primary Sources Info */}
        <Card className="mb-8" data-testid="primary-sources-card">
          <CardHeader>
            <CardTitle data-testid="primary-sources-title">Primary Sources</CardTitle>
            <CardDescription data-testid="primary-sources-description">
              For best results, upload these files first.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="flex items-start gap-3" data-testid="master-tour-info">
                <div className="bg-blue-100 p-2 rounded">
                  <FileText className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="font-medium">Master Tour Export</p>
                  <p className="text-sm text-slate-600">
                    Primary source for shows, venues, call times, docks
                  </p>
                </div>
              </div>
              
              <div className="flex items-start gap-3" data-testid="eventbrite-info">
                <div className="bg-blue-100 p-2 rounded">
                  <FileText className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="font-medium">Eventbrite Export</p>
                  <p className="text-sm text-slate-600">
                    VIP lists, ticketing, ADA access
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex gap-4" data-testid="action-buttons">
          <Button
            onClick={handleActivate}
            size="lg"
            className="flex-1"
            disabled={uploadedFiles.length === 0}
            data-testid="approve-activate-button"
          >
            Approve & Activate
          </Button>
          
          <Button
            variant="outline"
            size="lg"
            onClick={() => navigate("/admin")}
            data-testid="back-button"
          >
            Back
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Upload;
