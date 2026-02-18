import React, { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CheckCircle, AlertCircle, Send, Loader2, Phone } from "lucide-react";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";
import { useNavigate } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LiveStatus = ({ tour }) => {
  const [invocations, setInvocations] = useState([]);
  const [escalations, setEscalations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [testQuery, setTestQuery] = useState("");
  const [testPhone, setTestPhone] = useState("");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
    
    // Auto-refresh every 10 seconds
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, [tour.id]);

  const loadData = async () => {
    try {
      const [invocationsRes, escalationsRes] = await Promise.all([
        axios.get(`${API}/tours/${tour.id}/invocations?limit=50`),
        axios.get(`${API}/tours/${tour.id}/escalations`)
      ]);
      
      setInvocations(invocationsRes.data);
      setEscalations(escalationsRes.data);
    } catch (error) {
      console.error("Failed to load data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleTestQuery = async () => {
    if (!testQuery) {
      toast.error("Please enter a test query");
      return;
    }

    try {
      setTesting(true);
      const response = await axios.post(`${API}/query`, {
        tour_code: tour.tour_code,
        query: testQuery,
        phone_number: testPhone || undefined
      });
      
      setTestResult(response.data);
      toast.success("Query processed!");
      
      // Reload invocations
      await loadData();
      
      // Clear form
      setTestQuery("");
    } catch (error) {
      console.error("Query failed:", error);
      toast.error("Query processing failed");
    } finally {
      setTesting(false);
    }
  };

  const getPolicyBadge = (policy) => {
    const variants = {
      truth_record: { variant: "default", label: "Truth Record" },
      normalized: { variant: "secondary", label: "Normalized" },
      raw: { variant: "outline", label: "Raw" },
      refusal: { variant: "destructive", label: "Refusal" },
      escalate: { variant: "destructive", label: "Escalated" }
    };
    
    const config = variants[policy] || { variant: "outline", label: policy };
    return <Badge variant={config.variant} data-testid={`policy-badge-${policy}`}>{config.label}</Badge>;
  };

  const getConfidenceBadge = (confidence) => {
    if (confidence >= 0.9) return <Badge className="bg-green-600" data-testid="confidence-high">High ({(confidence * 100).toFixed(0)}%)</Badge>;
    if (confidence >= 0.7) return <Badge className="bg-yellow-600" data-testid="confidence-medium">Medium ({(confidence * 100).toFixed(0)}%)</Badge>;
    return <Badge variant="destructive" data-testid="confidence-low">Low ({(confidence * 100).toFixed(0)}%)</Badge>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen" data-testid="loading-spinner">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading status...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-12" data-testid="live-status-screen">
      <Toaster />
      
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold mb-2" data-testid="page-title">Live Status</h1>
              <p className="text-slate-600" data-testid="page-subtitle">
                Your tour is live. Test queries and monitor activity.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm font-mono bg-blue-100 text-blue-700 px-3 py-1 rounded" data-testid="tour-code-badge">
                {tour.tour_code}
              </span>
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 bg-green-500 rounded-full animate-pulse" data-testid="live-indicator"></div>
                <span className="text-sm font-medium" data-testid="live-label">LIVE</span>
              </div>
            </div>
          </div>
        </div>

        {/* Test SMS Interface */}
        <Card className="mb-8" data-testid="test-interface-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2" data-testid="test-interface-title">
              <Phone className="h-5 w-5" />
              Test Query Interface
            </CardTitle>
            <CardDescription data-testid="test-interface-description">
              Test TourText responses. In production, crew would text these queries.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid md:grid-cols-4 gap-4">
                <div className="md:col-span-3">
                  <Label htmlFor="test-query" data-testid="test-query-label">Query</Label>
                  <Input
                    id="test-query"
                    placeholder="e.g., What time is load-in tomorrow?"
                    value={testQuery}
                    onChange={(e) => setTestQuery(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleTestQuery()}
                    data-testid="test-query-input"
                  />
                </div>
                
                <div>
                  <Label htmlFor="test-phone" data-testid="test-phone-label">Phone (optional)</Label>
                  <Input
                    id="test-phone"
                    placeholder="+1234567890"
                    value={testPhone}
                    onChange={(e) => setTestPhone(e.target.value)}
                    data-testid="test-phone-input"
                  />
                </div>
              </div>

              <Button
                onClick={handleTestQuery}
                disabled={testing || !testQuery}
                data-testid="send-test-query-button"
              >
                {testing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    Send Test Query
                  </>
                )}
              </Button>

              {testResult && (
                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg" data-testid="test-result">
                  <div className="flex items-start justify-between mb-2">
                    <p className="font-medium text-blue-900" data-testid="test-result-title">Response:</p>
                    <div className="flex gap-2">
                      {getPolicyBadge(testResult.answer_policy)}
                      {getConfidenceBadge(testResult.confidence)}
                    </div>
                  </div>
                  <p className="text-slate-700 mb-2" data-testid="test-result-response">{testResult.response}</p>
                  <p className="text-xs text-slate-600" data-testid="test-result-taid">
                    Invocation TAID: {testResult.invocation_taid}
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Tabs: Recent Queries & Escalations */}
        <Tabs defaultValue="queries" data-testid="main-tabs">
          <TabsList className="grid w-full grid-cols-2" data-testid="tabs-list">
            <TabsTrigger value="queries" data-testid="queries-tab">
              Recent Queries ({invocations.length})
            </TabsTrigger>
            <TabsTrigger value="escalations" data-testid="escalations-tab">
              Escalations ({escalations.filter(e => e.status === "open").length})
            </TabsTrigger>
          </TabsList>

          {/* Recent Queries */}
          <TabsContent value="queries" data-testid="queries-content">
            <Card>
              <CardHeader>
                <CardTitle data-testid="queries-title">Recent Queries</CardTitle>
                <CardDescription data-testid="queries-description">
                  Last 50 invocations with confidence scores and answer policies.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {invocations.length === 0 ? (
                  <div className="text-center py-8 text-slate-600" data-testid="no-queries-message">
                    No queries yet. Send a test query above to get started.
                  </div>
                ) : (
                  <ScrollArea className="h-[500px]" data-testid="queries-scroll-area">
                    <div className="space-y-3">
                      {invocations.map((inv, index) => (
                        <div
                          key={inv.id}
                          className="p-4 bg-slate-50 rounded-lg"
                          data-testid={`invocation-${index}`}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <p className="font-medium" data-testid={`invocation-query-${index}`}>{inv.query_text}</p>
                            <div className="flex gap-2">
                              {getPolicyBadge(inv.answer_policy)}
                              {getConfidenceBadge(inv.confidence)}
                            </div>
                          </div>
                          
                          {inv.response_preview && (
                            <p className="text-sm text-slate-600 mb-2" data-testid={`invocation-response-${index}`}>
                              {inv.response_preview}
                            </p>
                          )}
                          
                          <div className="flex items-center justify-between text-xs text-slate-500">
                            <span data-testid={`invocation-taid-${index}`}>TAID: {inv.taid}</span>
                            <span data-testid={`invocation-latency-${index}`}>
                              {inv.latency_ms}ms • {new Date(inv.created_at).toLocaleString()}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Escalations */}
          <TabsContent value="escalations" data-testid="escalations-content">
            <Card>
              <CardHeader>
                <CardTitle data-testid="escalations-title">Escalations</CardTitle>
                <CardDescription data-testid="escalations-description">
                  Queries that require human review or missing information.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {escalations.length === 0 ? (
                  <div className="text-center py-8 text-slate-600" data-testid="no-escalations-message">
                    No escalations. All queries answered successfully.
                  </div>
                ) : (
                  <ScrollArea className="h-[500px]" data-testid="escalations-scroll-area">
                    <div className="space-y-3">
                      {escalations.map((esc, index) => (
                        <div
                          key={esc.id}
                          className={`p-4 rounded-lg border ${
                            esc.status === "open"
                              ? "bg-red-50 border-red-200"
                              : "bg-slate-50 border-slate-200"
                          }`}
                          data-testid={`escalation-${index}`}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <p className="font-medium" data-testid={`escalation-type-${index}`}>
                                {esc.escalation_type.replace(/_/g, " ").toUpperCase()}
                              </p>
                              <p className="text-sm text-slate-600" data-testid={`escalation-description-${index}`}>
                                {esc.description}
                              </p>
                            </div>
                            <Badge
                              variant={esc.status === "open" ? "destructive" : "secondary"}
                              data-testid={`escalation-status-badge-${index}`}
                            >
                              {esc.status}
                            </Badge>
                          </div>
                          
                          <div className="flex items-center justify-between text-xs text-slate-500 mt-2">
                            <span data-testid={`escalation-taid-${index}`}>TAID: {esc.taid}</span>
                            <span data-testid={`escalation-severity-${index}`}>
                              Severity: {esc.severity} • {new Date(esc.created_at).toLocaleString()}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Back Button */}
        <div className="mt-8">
          <Button
            variant="outline"
            onClick={() => navigate("/admin")}
            data-testid="back-to-tours-button"
          >
            Back to Tours
          </Button>
        </div>
      </div>
    </div>
  );
};

export default LiveStatus;
