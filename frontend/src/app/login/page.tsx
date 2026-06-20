"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, Loader2 } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const { data, error: authError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (authError) {
      setError(authError.message);
      setLoading(false);
      return;
    }

    if (data.session) {
      // Clear legacy mock_user
      localStorage.removeItem("mock_user");
      router.push("/dashboard");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-indigo-50 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8 flex flex-col items-center">
          <img src="/logo.jpeg" alt="BIW OS Logo" className="w-16 h-16 rounded-xl mb-4 shadow-sm object-cover" />
          <h1 className="text-3xl font-bold tracking-tight text-indigo-900 mb-2">BIW OS</h1>
          <p className="text-slate-600">Sign in to manage your system</p>
        </div>

        <Card className="bg-white border-slate-200 shadow-xl">
          <CardHeader>
            <CardTitle className="text-xl text-slate-900">Welcome back</CardTitle>
            <CardDescription className="text-slate-500">Enter your credentials to access the system.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              {error && (
                <Alert variant="destructive" className="bg-red-500/10 border-red-500/20 text-red-400">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Email address</label>
                <Input
                  type="email"
                  required
                  placeholder="name@biw.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="bg-slate-50 border-slate-200 text-slate-900"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Password</label>
                <Input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="bg-slate-50 border-slate-200 text-slate-900"
                />
              </div>

              <Button
                type="submit"
                className="w-full bg-indigo-500 hover:bg-indigo-600 text-white"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  "Sign in"
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
        <p className="text-center text-sm text-slate-500 mt-8">
          Don't have an account? Contact your BIW owner to request access.
        </p>
      </div>
    </div>
  );
}
