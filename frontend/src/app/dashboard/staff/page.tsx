"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { createUser, fetchAllRooms, fetchAllUsers } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AlertCircle, CheckCircle2, Loader2, UserPlus, ShieldAlert } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function StaffManagementPage() {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    role: "therapist",
    room_id: ""
  });

  // Check if current user is owner (in real app, we'd check their role token)
  const { data: users, isLoading: loadingUsers } = useQuery({
    queryKey: ['admin-users'],
    queryFn: fetchAllUsers
  });

  const { data: rooms } = useQuery({
    queryKey: ['admin-rooms'],
    queryFn: fetchAllRooms
  });

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      setSuccess(true);
      setError(null);
      setFormData({ name: "", email: "", password: "", role: "therapist", room_id: "" });
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      setTimeout(() => setSuccess(false), 5000);
    },
    onError: (err: any) => {
      setError(err.message);
      setSuccess(false);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  return (
    <div className="flex-1 overflow-auto bg-slate-50 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
            <UserPlus className="h-8 w-8 text-indigo-500" />
            Staff Management
          </h1>
          <p className="text-slate-500 mt-2">Provision new employee accounts and assign them to branches.</p>
          <Alert className="mt-4 bg-amber-500/10 border-amber-500/20 text-amber-500">
            <ShieldAlert className="h-4 w-4" />
            <AlertDescription>
              This area is highly restricted. Only Owners can create new staff accounts. Accounts created here bypass email verification and are active immediately.
            </AlertDescription>
          </Alert>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <Card className="lg:col-span-1 bg-white border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl text-slate-900">Create Account</CardTitle>
              <CardDescription className="text-slate-500">Fill out the details for the new staff member.</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <Alert variant="destructive" className="bg-red-500/10 border-red-500/20 text-red-400 p-3">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription className="text-xs">{error}</AlertDescription>
                  </Alert>
                )}
                {success && (
                  <Alert className="bg-green-500/10 border-green-500/20 text-green-400 p-3">
                    <CheckCircle2 className="h-4 w-4" />
                    <AlertDescription className="text-xs">User successfully created.</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-700">Full Name</label>
                  <Input required placeholder="Jane Doe" value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} className="bg-slate-50 border-slate-200 text-slate-900" />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-700">Email Address</label>
                  <Input type="email" required placeholder="jane@clinic.com" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} className="bg-slate-50 border-slate-200 text-slate-900" />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-700">Temporary Password</label>
                  <Input type="text" required placeholder="password123" value={formData.password} onChange={(e) => setFormData({...formData, password: e.target.value})} className="bg-slate-50 border-slate-200 text-slate-900" />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-700">Role</label>
                  <Select value={formData.role} onValueChange={(val) => setFormData({...formData, role: val || "therapist"})}>
                    <SelectTrigger className="bg-slate-50 border-slate-200 text-slate-900">
                      <SelectValue placeholder="Select role" />
                    </SelectTrigger>
                    <SelectContent className="bg-white border-slate-200 text-slate-900">
                      <SelectItem value="therapist">Therapist</SelectItem>
                      <SelectItem value="manager">Branch Manager</SelectItem>
                      <SelectItem value="hr">HR</SelectItem>
                      <SelectItem value="it_team">IT Support</SelectItem>
                      <SelectItem value="executive">Executive</SelectItem>
                      <SelectItem value="cleaner">Cleaner</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-700">Initial Branch / Department</label>
                  <Select value={formData.room_id} onValueChange={(val) => setFormData({...formData, room_id: val || ""})}>
                    <SelectTrigger className="bg-slate-50 border-slate-200 text-slate-900">
                      <SelectValue placeholder="Select branch" />
                    </SelectTrigger>
                    <SelectContent className="bg-white border-slate-200 text-slate-900">
                      {rooms?.map((r: any) => (
                        <SelectItem key={r.id} value={r.id}>{r.name} ({r.type})</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <Button type="submit" disabled={createMutation.isPending} className="w-full bg-indigo-500 hover:bg-indigo-600 text-white mt-4">
                  {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <UserPlus className="h-4 w-4 mr-2" />}
                  Provision Account
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card className="lg:col-span-2 bg-white border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl text-slate-900">Active Staff Directory</CardTitle>
              <CardDescription className="text-slate-500">All users currently in the system.</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingUsers ? (
                <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-slate-400" /></div>
              ) : (
                <div className="flex flex-col gap-3">
                  {users?.map((user: any) => (
                    <div key={user.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50 transition-colors">
                      <div className="flex flex-col min-w-0">
                        <p className="font-semibold text-slate-900 truncate">{user.name}</p>
                        <p className="text-sm text-slate-500 truncate">{user.email}</p>
                      </div>
                      <div className="flex-shrink-0">
                        <span className="bg-white px-3 py-1 rounded-md text-xs font-medium capitalize text-slate-600 border border-slate-200 shadow-sm inline-block">
                          {user.role.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
