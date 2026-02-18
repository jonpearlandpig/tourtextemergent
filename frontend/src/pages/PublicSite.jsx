import React from "react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Clock, Shield, Zap } from "lucide-react";

const PublicSite = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-20">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-6xl font-bold mb-6" data-testid="hero-title">
            Tour information.
            <br />
            <span className="text-blue-400">Instantly usable under pressure.</span>
          </h1>
          
          <p className="text-xl text-slate-300 mb-12 max-w-2xl mx-auto" data-testid="hero-description">
            TourText activates your existing tour systems and makes information accessible via text.
            No behavior change. No replacement. Just instant answers when you need them.
          </p>
          
          <div className="flex gap-4 justify-center" data-testid="hero-cta-buttons">
            <Button
              size="lg"
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-6 text-lg"
              onClick={() => navigate("/admin")}
              data-testid="start-tour-button"
            >
              Start a Tour
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            
            <Button
              size="lg"
              variant="outline"
              className="border-slate-600 text-white hover:bg-slate-800 px-8 py-6 text-lg"
              onClick={() => navigate("/admin")}
              data-testid="sign-in-button"
            >
              Sign In
            </Button>
          </div>
        </div>
      </div>

      {/* 60-Second Activation Path */}
      <div className="bg-slate-800/50 py-20" data-testid="activation-section">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-4xl font-bold text-center mb-4" data-testid="activation-title">
              The 60-Second Activation Path
            </h2>
            <p className="text-xl text-slate-300 text-center mb-12" data-testid="activation-subtitle">
              From upload to first usable response in under 90 seconds.
            </p>
            
            <div className="grid md:grid-cols-3 gap-8">
              <div className="bg-slate-900/50 p-8 rounded-lg border border-slate-700" data-testid="step-1">
                <div className="flex items-center gap-3 mb-4">
                  <div className="bg-blue-600 text-white w-10 h-10 rounded-full flex items-center justify-center font-bold">
                    1
                  </div>
                  <h3 className="text-xl font-bold">Export</h3>
                </div>
                <p className="text-slate-300">
                  Export from Master Tour or Eventbrite. Zero behavior change.
                </p>
              </div>
              
              <div className="bg-slate-900/50 p-8 rounded-lg border border-slate-700" data-testid="step-2">
                <div className="flex items-center gap-3 mb-4">
                  <div className="bg-blue-600 text-white w-10 h-10 rounded-full flex items-center justify-center font-bold">
                    2
                  </div>
                  <h3 className="text-xl font-bold">Upload</h3>
                </div>
                <p className="text-slate-300">
                  Drag and drop into TourText. Automatic detection and indexing.
                </p>
              </div>
              
              <div className="bg-slate-900/50 p-8 rounded-lg border border-slate-700" data-testid="step-3">
                <div className="flex items-center gap-3 mb-4">
                  <div className="bg-blue-600 text-white w-10 h-10 rounded-full flex items-center justify-center font-bold">
                    3
                  </div>
                  <h3 className="text-xl font-bold">Live</h3>
                </div>
                <p className="text-slate-300">
                  Text to test. Live answers backed by your documents.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Use Cases */}
      <div className="py-20" data-testid="use-cases-section">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-4xl font-bold text-center mb-16" data-testid="use-cases-title">Proven in the Field</h2>
            
            <div className="space-y-12">
              {/* Use Case 1 */}
              <div className="bg-slate-800/30 p-8 rounded-lg border border-slate-700" data-testid="use-case-docks">
                <div className="flex items-start gap-4">
                  <div className="bg-blue-600 p-3 rounded-lg">
                    <Clock className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold mb-2">2:47 AM Dock Query</h3>
                    <p className="text-slate-300 mb-4">
                      Production manager texts: "Which dock for Salt Lake tomorrow?"
                      TourText responds in 3 seconds with verified dock info from Master Tour.
                    </p>
                    <p className="text-sm text-slate-400">
                      No radio traffic. No waking the TM. No digging through PDFs.
                    </p>
                  </div>
                </div>
              </div>

              {/* Use Case 2 */}
              <div className="bg-slate-800/30 p-8 rounded-lg border border-slate-700" data-testid="use-case-vip">
                <div className="flex items-start gap-4">
                  <div className="bg-blue-600 p-3 rounded-lg">
                    <Shield className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold mb-2">VIP & ADA Access</h3>
                    <p className="text-slate-300 mb-4">
                      Guest services: "ADA entry for tonight?" Instant response from Eventbrite data with
                      gate, time, and contact person.
                    </p>
                    <p className="text-sm text-slate-400">
                      Critical accessibility info available instantly, not buried in email threads.
                    </p>
                  </div>
                </div>
              </div>

              {/* Use Case 3 */}
              <div className="bg-slate-800/30 p-8 rounded-lg border border-slate-700" data-testid="use-case-settlement">
                <div className="flex items-start gap-4">
                  <div className="bg-blue-600 p-3 rounded-lg">
                    <Zap className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold mb-2">11 PM Settlement Discrepancy</h3>
                    <p className="text-slate-300 mb-4">
                      Tour accountant: "What was the guarantee for tonight?" TourText returns settlement
                      terms with source reference and confidence score.
                    </p>
                    <p className="text-sm text-slate-400">
                      Financial guardrails ensure no guessing. Escalates if unverified.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* What TourText Is NOT */}
      <div className="bg-slate-800/50 py-20" data-testid="not-section">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-8" data-testid="not-title">What TourText Is Not</h2>
            
            <div className="space-y-4 text-lg text-slate-300">
              <p data-testid="not-chatbot">• <strong className="text-white">Not a chatbot.</strong> It retrieves verified information, not guesses.</p>
              <p data-testid="not-replacement">• <strong className="text-white">Not a replacement for Master Tour.</strong> It activates your existing system.</p>
              <p data-testid="not-workflow">• <strong className="text-white">Not a workflow tool.</strong> It makes existing workflows instantly accessible.</p>
              <p data-testid="not-extra-step">• <strong className="text-white">Not an extra step.</strong> If it feels like one, it has failed.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Final CTA */}
      <div className="py-20" data-testid="final-cta-section">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-4xl font-bold mb-6" data-testid="final-cta-title">
            Ready to activate your tour information?
          </h2>
          <Button
            size="lg"
            className="bg-blue-600 hover:bg-blue-700 text-white px-12 py-6 text-lg"
            onClick={() => navigate("/admin")}
            data-testid="final-cta-button"
          >
            Get Started
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-700 py-8" data-testid="footer">
        <div className="container mx-auto px-4 text-center text-slate-400">
          <p>TourText™ v4.1 — Infrastructure-grade tour information system</p>
          <p className="text-sm mt-2">Pearl & Pig — GoGarvis Runtime + Telauthorium Provenance</p>
        </div>
      </footer>
    </div>
  );
};

export default PublicSite;
