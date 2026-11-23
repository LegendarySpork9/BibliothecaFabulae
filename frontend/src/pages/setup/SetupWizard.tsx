import axios from "axios";
import { useEffect, useState } from "react";

import { setAccessToken } from "../../api/client";
import { AccountStep } from "./steps/AccountStep";
import { SmtpStep } from "./steps/SmtpStep";
import { StorageStep } from "./steps/StorageStep";
import { SummaryStep } from "./steps/SummaryStep";
import { TotpStep } from "./steps/TotpStep";

const STEPS = ["Account", "2FA Setup", "Storage", "Email", "Summary"];

export function SetupWizard() {
  const [currentStep, setCurrentStep] = useState(0);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    axios
      .get("/api/setup/status")
      .then((res) => {
        const step = res.data.current_step;

        if (step > 1) {
          setCurrentStep(step - 1);
        }

        if (res.data.storage_path) {
          setStoragePath(res.data.storage_path);
        }

        if (res.data.smtp_configured) {
          setSmtpConfigured(true);
        }
        
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, []);

  const [totpData, setTotpData] = useState<{
    qr_code_base64: string;
    totp_secret: string;
  } | null>(null);
  const [storagePath, setStoragePath] = useState("");
  const [smtpConfigured, setSmtpConfigured] = useState(false);

  const handleComplete = (accessToken: string) => {
    setAccessToken(accessToken);
    window.location.href = "/dashboard";
  };

  if (!loaded) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Step indicator */}
        <div className="mb-8">
          <div className="flex items-start">
            {STEPS.map((label, i) => (
              <div key={label} className="flex items-start flex-1">
                <div className="flex flex-col items-center w-full">
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-medium ${
                      i < currentStep
                        ? "bg-indigo-600 text-white"
                        : i === currentStep
                          ? "bg-indigo-600 text-white ring-4 ring-indigo-100 dark:ring-indigo-900"
                          : "bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400"
                    }`}
                  >
                    {i + 1}
                  </div>
                  <span className="mt-2 text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                    {label}
                  </span>
                </div>
                {i < STEPS.length - 1 ? (
                  <div
                    className={`h-0.5 shrink-0 w-10 mt-4 -mx-2 ${
                      i < currentStep
                        ? "bg-indigo-600"
                        : "bg-gray-200 dark:bg-gray-700"
                    }`}
                  />
                ) : (
                  <div className="shrink-0 w-10 -mx-2" />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step content */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
          {currentStep === 0 && (
            <AccountStep
              onNext={(data) => {
                setTotpData(data);
                setCurrentStep(1);
              }}
            />
          )}
          {currentStep === 1 && totpData && (
            <TotpStep
              qrCodeBase64={totpData.qr_code_base64}
              totpSecret={totpData.totp_secret}
              onNext={() => setCurrentStep(2)}
              onBack={() => setCurrentStep(0)}
            />
          )}
          {currentStep === 2 && (
            <StorageStep
              onNext={(path) => {
                setStoragePath(path);
                setCurrentStep(3);
              }}
              onBack={() => setCurrentStep(1)}
            />
          )}
          {currentStep === 3 && (
            <SmtpStep
              onNext={(configured) => {
                setSmtpConfigured(configured);
                setCurrentStep(4);
              }}
              onBack={() => setCurrentStep(2)}
            />
          )}
          {currentStep === 4 && (
            <SummaryStep
              storagePath={storagePath}
              smtpConfigured={smtpConfigured}
              onComplete={handleComplete}
              onBack={() => setCurrentStep(3)}
            />
          )}
        </div>
      </div>
    </div>
  );
}
