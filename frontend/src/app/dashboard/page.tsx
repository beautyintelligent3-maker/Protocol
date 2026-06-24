"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchTickets, fetchTicketDetails, postMessage, updateTicket,
  fetchAllUsers, fetchAllRooms, approveTicket, fetchCurrentUser,
} from "@/lib/api";
import { useSearchParams, useRouter } from "next/navigation";
import { Suspense, useState, useEffect } from "react";
import {
  Loader2, Ticket, CheckCircle2, AlertCircle, ArrowLeft,
  Paperclip, Download, X, Search, Activity, RotateCcw,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { CreateTicketDialog } from "@/components/CreateTicketDialog";
import { supabase } from "@/lib/supabase";
import { getSlug } from "./layout";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function toLocalDatetimeValue(utcDate: string): string {
  const d = new Date(utcDate);
  return [
    d.getFullYear(),
    String(d.getMonth() + 1).padStart(2, "0"),
    String(d.getDate()).padStart(2, "0"),
  ].join("-") + "T" + [
    String(d.getHours()).padStart(2, "0"),
    String(d.getMinutes()).padStart(2, "0"),
  ].join(":");
}

function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString("en-GB", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function PropLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1.5">
      {children}
    </p>
  );
}

function DashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const roomSlug = searchParams.get("room");
  const roomFallbackId = searchParams.get("room_id");
  const ticketId = searchParams.get("ticket_id");

  const [filterStaffId, setFilterStaffId] = useState("");
  const [filterStatus, setFilterStatus] = useState<"active" | "resolved">("active");
  const [comment, setComment] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dueDate, setDueDate] = useState("");

  const queryClient = useQueryClient();

  useEffect(() => {
    const channel = supabase
      .channel("dashboard_changes")
      .on("postgres_changes", { event: "*", schema: "public", table: "messages" }, () => {
        if (ticketId) queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
      })
      .on("postgres_changes", { event: "*", schema: "public", table: "tickets" }, () => {
        queryClient.invalidateQueries({ queryKey: ["tickets"] });
        if (ticketId) queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
      })
      .subscribe();
    return () => { supabase.removeChannel(channel); };
  }, [ticketId, queryClient]);

  const { data: allRooms } = useQuery({ queryKey: ["allRooms"], queryFn: fetchAllRooms });
  const roomId = roomSlug
    ? allRooms?.find((r: any) => getSlug(r.name) === roomSlug)?.id
    : roomFallbackId;

  const { data: fetchedTickets, isLoading, error } = useQuery({
    queryKey: ["tickets", roomId, filterStaffId],
    queryFn: () => fetchTickets({ room_id: roomId || undefined, assignee_staff_id: filterStaffId || undefined }),
    enabled: roomSlug ? !!roomId : true,
  });

  const tickets = fetchedTickets
    ? [...fetchedTickets]
        .filter((t: any) =>
          filterStatus === "resolved" ? t.status === "resolved" : t.status !== "resolved"
        )
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    : [];

  const { data: selectedTicket, isLoading: isTicketLoading, error: ticketError } = useQuery({
    queryKey: ["ticket", ticketId],
    queryFn: () => fetchTicketDetails(ticketId as string),
    enabled: !!ticketId,
  });

  useEffect(() => {
    setDueDate(selectedTicket?.due_date ? toLocalDatetimeValue(selectedTicket.due_date) : "");
  }, [selectedTicket?.id]);

  const postMessageMutation = useMutation({
    mutationFn: (data: { content: string; file?: File | null }) =>
      postMessage(ticketId as string, data.content, "comment", data.file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
      setComment("");
      setSelectedFile(null);
    },
  });

  const updateTicketMutation = useMutation({
    mutationFn: (updates: any) => updateTicket(ticketId as string, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
    },
  });

  const { data: allUsers } = useQuery({ queryKey: ["allUsers"], queryFn: fetchAllUsers });
  const { data: currentUser } = useQuery({ queryKey: ["currentUser"], queryFn: fetchCurrentUser });
  const currentUserRole = currentUser?.role || "";

  const approveTicketMutation = useMutation({
    mutationFn: () => approveTicket(ticketId as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
    },
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case "open": return "bg-blue-50 text-blue-700 border-blue-200";
      case "in_progress": return "bg-amber-50 text-amber-700 border-amber-200";
      case "approved": return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "resolved": return "bg-slate-100 text-slate-500 border-slate-200";
      default: return "bg-slate-100 text-slate-500 border-slate-200";
    }
  };

  const getPriorityDot = (priority: string) => {
    switch (priority) {
      case "high": return "bg-red-500";
      case "medium": return "bg-amber-500";
      case "low": return "bg-green-500";
      default: return "bg-slate-400";
    }
  };

  const getPriorityTextColor = (priority: string) => {
    switch (priority) {
      case "high": return "text-red-600";
      case "medium": return "text-amber-600";
      case "low": return "text-green-600";
      default: return "text-slate-500";
    }
  };

  const isOverdue =
    selectedTicket?.due_date &&
    new Date(selectedTicket.due_date) < new Date() &&
    selectedTicket.status !== "resolved";

  const handleDueDateBlur = () => {
    if (!selectedTicket) return;
    const currentVal = selectedTicket.due_date
      ? toLocalDatetimeValue(selectedTicket.due_date)
      : "";
    if (dueDate !== currentVal) {
      updateTicketMutation.mutate({
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
      });
    }
  };

  const assigneeId =
    selectedTicket?.assignee?.id ||
    (typeof selectedTicket?.assignee === "string" ? selectedTicket.assignee : null) ||
    null;

  const resolvedAssigneeName = (() => {
    if (!assigneeId) return null;
    const found = allUsers?.find((u: any) => u.id === assigneeId);
    if (found) return `${found.staff_id ? `[${found.staff_id}] ` : ""}${found.name}`;
    if (selectedTicket?.assignee && typeof selectedTicket.assignee === "object") {
      return selectedTicket.assignee.name;
    }
    return null;
  })();

  const goBack = () => {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("ticket_id");
    router.push(`/dashboard?${params.toString()}`);
  };

  const roomName = roomId
    ? allRooms?.find((r: any) => r.id === roomId)?.name
    : "All Tickets";

  return (
    <div className="flex flex-1 h-full overflow-hidden bg-white">

      {/* ── LEFT: Ticket List ── */}
      <div
        className={`flex flex-col border-r border-slate-200 flex-shrink-0 ${
          ticketId ? "w-[300px] hidden md:flex" : "w-full"
        }`}
      >
        {/* List header */}
        <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Ticket className="w-4 h-4 text-slate-400" />
            <h2 className="text-sm font-semibold text-slate-800 truncate">{roomName}</h2>
          </div>
          {["owner", "manager", "hr", "it_team"].includes(currentUserRole) && (
            <CreateTicketDialog roomId={roomId} />
          )}
        </div>

        {/* Filters */}
        <div className="px-3 py-2.5 border-b border-slate-200 space-y-2 bg-slate-50">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
            <Input
              placeholder="Search by Staff ID"
              value={filterStaffId}
              onChange={(e) => setFilterStaffId(e.target.value)}
              className="pl-8 h-8 bg-white text-sm border-slate-200"
            />
          </div>
          <div className="flex bg-slate-200/60 p-0.5 rounded-md gap-0.5">
            {(["active", "resolved"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilterStatus(f)}
                className={`flex-1 text-xs py-1.5 font-medium rounded transition-colors capitalize ${
                  filterStatus === f
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-500 hover:text-slate-700"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Ticket list */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="p-8 flex justify-center">
              <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
            </div>
          ) : error ? (
            <p className="p-4 text-center text-red-500 text-xs">Failed to load tickets.</p>
          ) : tickets.length === 0 ? (
            <p className="p-8 text-center text-slate-400 text-sm">No tickets found.</p>
          ) : (
            <div className="divide-y divide-slate-100">
              {tickets.map((ticket: any) => (
                <button
                  key={ticket.id}
                  onClick={() => {
                    const params = new URLSearchParams(searchParams.toString());
                    params.set("ticket_id", ticket.id);
                    if (roomSlug) params.set("room", roomSlug);
                    else if (roomId) params.set("room_id", roomId);
                    router.push(`/dashboard?${params.toString()}`);
                  }}
                  className={`w-full text-left p-3.5 transition-colors hover:bg-slate-50 relative ${
                    ticket.id === ticketId
                      ? "bg-indigo-50/50 shadow-[inset_3px_0_0_0_#6366f1]"
                      : ""
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 ${getPriorityTextColor(ticket.priority)}`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${getPriorityDot(ticket.priority)}`} />
                      {ticket.priority}
                    </span>
                    <Badge
                      variant="secondary"
                      className={`text-[10px] uppercase font-bold border-none px-1.5 py-0.5 ${getStatusColor(ticket.status)}`}
                    >
                      {ticket.status.replace("_", " ")}
                    </Badge>
                  </div>
                  <h3 className="font-medium text-slate-900 text-sm leading-snug line-clamp-2 mb-2">
                    {ticket.title}
                  </h3>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400 truncate">{ticket.creator.name}</span>
                    <span className="text-xs text-slate-400 shrink-0 ml-2">
                      {new Date(ticket.created_at).toLocaleDateString("en-GB", {
                        day: "2-digit", month: "short",
                      })}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── RIGHT: Ticket Detail ── */}
      {ticketId ? (
        <div className="flex-1 flex flex-col overflow-hidden">
          {isTicketLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <Loader2 className="w-7 h-7 animate-spin text-indigo-500" />
            </div>
          ) : ticketError ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
              <AlertCircle className="w-10 h-10 text-red-400 mb-3" />
              <p className="font-semibold text-slate-800">Failed to load ticket</p>
              <p className="text-sm text-slate-500 mt-1">
                {(ticketError as Error).message}
              </p>
            </div>
          ) : selectedTicket ? (
            <div className="flex-1 flex overflow-hidden">

              {/* ── MAIN COLUMN ── */}
              <div className="flex-1 overflow-y-auto flex flex-col min-w-0">

                {/* Header */}
                <div className="bg-white border-b border-slate-200 px-5 py-4 flex-shrink-0">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="md:hidden mb-3 -ml-1 text-slate-500 h-8 text-xs"
                    onClick={goBack}
                  >
                    <ArrowLeft className="w-3.5 h-3.5 mr-1" />
                    Back
                  </Button>

                  <div className="flex items-start gap-3 justify-between flex-wrap">
                    <div className="flex-1 min-w-0">
                      {/* Status row */}
                      <div className="flex items-center flex-wrap gap-1.5 mb-2.5">
                        <Badge
                          className={`text-[10px] uppercase tracking-widest font-bold border px-2 py-0.5 ${getStatusColor(selectedTicket.status)}`}
                        >
                          {selectedTicket.status.replace("_", " ")}
                        </Badge>
                        {selectedTicket.approval_status === "pending" && (
                          <Badge className="text-[10px] uppercase tracking-widest font-bold bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5">
                            Pending Approval
                          </Badge>
                        )}
                        {isOverdue && (
                          <Badge className="text-[10px] uppercase tracking-widest font-bold bg-red-50 text-red-600 border border-red-200 px-2 py-0.5 animate-pulse">
                            Overdue
                          </Badge>
                        )}
                      </div>
                      <h1 className="text-lg font-bold text-slate-900 leading-snug">
                        {selectedTicket.title}
                      </h1>
                    </div>

                    {/* Action buttons */}
                    <div className="flex gap-2 shrink-0">
                      {selectedTicket.approval_status === "pending" &&
                        currentUserRole === "owner" && (
                          <Button
                            size="sm"
                            className="bg-amber-500 hover:bg-amber-600 text-white h-8 text-xs"
                            onClick={() => approveTicketMutation.mutate()}
                            disabled={approveTicketMutation.isPending}
                          >
                            <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                            Approve
                          </Button>
                        )}
                      {selectedTicket.status !== "resolved" ? (
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-emerald-600 border-emerald-200 hover:bg-emerald-50 h-8 text-xs"
                          onClick={() => updateTicketMutation.mutate({ status: "resolved" })}
                          disabled={updateTicketMutation.isPending}
                        >
                          <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                          Mark Resolved
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-amber-600 border-amber-200 hover:bg-amber-50 h-8 text-xs"
                          onClick={() => updateTicketMutation.mutate({ status: "open" })}
                          disabled={updateTicketMutation.isPending}
                        >
                          <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
                          Re-open
                        </Button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Description */}
                <div className="bg-[#f7f6f3] border-b border-slate-200 px-5 py-4 flex-shrink-0">
                  <PropLabel>Description</PropLabel>
                  <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                    {selectedTicket.description}
                  </p>
                </div>

                {/* Activity Feed */}
                <div className="bg-[#f7f6f3] flex-1 px-5 py-4">
                  <PropLabel>
                    <span className="flex items-center gap-1.5">
                      <Activity className="w-3 h-3" />
                      Activity
                    </span>
                  </PropLabel>

                  {/* Timeline */}
                  <div className="relative pl-6 border-l-2 border-slate-200 ml-2 mt-3 space-y-0">

                    {/* Ticket opened event */}
                    <div className="flex items-center gap-3 py-1.5 -ml-[19px]">
                      <div className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 text-[10px] font-bold flex items-center justify-center shrink-0 ring-2 ring-white">
                        {selectedTicket.creator?.name?.charAt(0)}
                      </div>
                      <span className="text-xs text-slate-500">
                        <span className="font-semibold text-slate-700">
                          {selectedTicket.creator?.name}
                        </span>{" "}
                        opened this ticket
                      </span>
                      <span className="text-xs text-slate-400 ml-auto shrink-0">
                        {formatDateTime(selectedTicket.created_at)}
                      </span>
                    </div>

                    {/* Messages */}
                    {selectedTicket.messages?.map((msg: any) => {
                      if (msg.type === "status_update" || msg.type === "approval") {
                        return (
                          <div key={msg.id} className="flex items-center gap-3 py-1.5 -ml-[13px]">
                            <div className="w-4 h-4 rounded-full bg-white border-2 border-slate-300 flex items-center justify-center shrink-0">
                              <div className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                            </div>
                            <span className="text-xs text-slate-500">
                              <span className="font-semibold text-slate-600">
                                {msg.author.name}
                              </span>{" "}
                              {msg.content.toLowerCase()}
                            </span>
                            <span className="text-xs text-slate-400 ml-auto shrink-0">
                              {formatDateTime(msg.created_at)}
                            </span>
                          </div>
                        );
                      }

                      return (
                        <div key={msg.id} className="py-2 -ml-[19px]">
                          <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 ml-2">
                            <div className="flex items-start gap-3">
                              <div className="w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center shrink-0">
                                {msg.author.name.charAt(0)}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-baseline gap-2 mb-2 flex-wrap">
                                  <span className="text-sm font-semibold text-slate-800">
                                    {msg.author.name}
                                  </span>
                                  {msg.author.staff_id && (
                                    <span className="text-xs text-slate-400 font-mono">
                                      [{msg.author.staff_id}]
                                    </span>
                                  )}
                                  <span className="text-xs text-slate-400 ml-auto shrink-0">
                                    {formatDateTime(msg.created_at)}
                                  </span>
                                </div>
                                <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                                  {msg.content}
                                </p>
                                {msg.attachment_name && (
                                  <a
                                    href={`${API_BASE}/tickets/messages/${msg.id}/attachment`}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="inline-flex items-center gap-1.5 mt-3 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-600 hover:bg-slate-100 transition-colors"
                                  >
                                    <Paperclip className="w-3 h-3" />
                                    {msg.attachment_name}
                                    <Download className="w-3 h-3 opacity-50" />
                                  </a>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}

                    {selectedTicket.messages?.length === 0 && (
                      <p className="text-xs text-slate-400 py-4">No activity yet.</p>
                    )}
                  </div>

                  {/* Add Comment */}
                  <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4 mt-5">
                    <PropLabel>Add Comment</PropLabel>
                    {selectedFile && (
                      <div className="mb-2">
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-slate-50 border border-slate-200 rounded text-xs text-slate-600">
                          <Paperclip className="w-3 h-3" />
                          <span className="max-w-[180px] truncate">{selectedFile.name}</span>
                          <button onClick={() => setSelectedFile(null)}>
                            <X className="w-3 h-3 ml-0.5 text-slate-400 hover:text-slate-700" />
                          </button>
                        </span>
                      </div>
                    )}
                    <Textarea
                      placeholder="Write a comment..."
                      className="min-h-[80px] border-slate-200 text-sm resize-none focus-visible:ring-1 focus-visible:ring-slate-300"
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                    />
                    <div className="flex justify-between items-center mt-3 pt-3 border-t border-slate-100">
                      <div>
                        <input
                          type="file"
                          id="file-upload"
                          className="hidden"
                          onChange={(e) => {
                            if (e.target.files?.[0]) setSelectedFile(e.target.files[0]);
                          }}
                        />
                        <label
                          htmlFor="file-upload"
                          className="cursor-pointer inline-flex items-center justify-center w-8 h-8 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
                        >
                          <Paperclip className="w-4 h-4" />
                        </label>
                      </div>
                      <Button
                        size="sm"
                        className="h-8 text-xs"
                        disabled={(!comment.trim() && !selectedFile) || postMessageMutation.isPending}
                        onClick={() => postMessageMutation.mutate({ content: comment, file: selectedFile })}
                      >
                        {postMessageMutation.isPending ? (
                          <><Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />Posting…</>
                        ) : (
                          "Post Comment"
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              {/* ── PROPERTIES PANEL ── */}
              <div className="w-64 flex-shrink-0 border-l border-slate-200 bg-white overflow-y-auto hidden md:block">
                <div className="p-4 space-y-4">

                  {/* Status */}
                  <div>
                    <PropLabel>Status</PropLabel>
                    <Badge
                      className={`text-[10px] uppercase tracking-widest font-bold border px-2 py-0.5 ${getStatusColor(selectedTicket.status)}`}
                    >
                      {selectedTicket.status.replace("_", " ")}
                    </Badge>
                    {selectedTicket.approval_status === "pending" && (
                      <Badge className="ml-1 text-[10px] uppercase tracking-widest font-bold bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5">
                        Pending
                      </Badge>
                    )}
                  </div>

                  {/* Priority */}
                  <div>
                    <PropLabel>Priority</PropLabel>
                    <Select
                      value={selectedTicket.priority}
                      onValueChange={(val) => updateTicketMutation.mutate({ priority: val })}
                      disabled={updateTicketMutation.isPending || selectedTicket.status === "resolved"}
                    >
                      <SelectTrigger className="h-8 w-full border-slate-200 text-xs bg-slate-50 hover:bg-slate-100">
                        <div className="flex items-center gap-1.5">
                          <div className={`w-2 h-2 rounded-full ${getPriorityDot(selectedTicket.priority)}`} />
                          <span className="capitalize">{selectedTicket.priority}</span>
                        </div>
                      </SelectTrigger>
                      <SelectContent>
                        {["low", "medium", "high"].map((p) => (
                          <SelectItem key={p} value={p} className="text-xs capitalize">
                            {p.charAt(0).toUpperCase() + p.slice(1)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Assignee */}
                  <div>
                    <PropLabel>Assignee</PropLabel>
                    <Select
                      value={assigneeId || "unassigned"}
                      onValueChange={(val) =>
                        updateTicketMutation.mutate({
                          assigned_to_id: val === "unassigned" ? null : val,
                        })
                      }
                      disabled={updateTicketMutation.isPending || selectedTicket.status === "resolved"}
                    >
                      <SelectTrigger className="h-8 w-full border-slate-200 text-xs bg-slate-50 hover:bg-slate-100">
                        <div className="flex items-center gap-1.5 truncate">
                          <div className="w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 text-[10px] font-bold flex items-center justify-center shrink-0">
                            {resolvedAssigneeName ? resolvedAssigneeName.replace(/\[.*?\]\s*/, "").charAt(0) : "?"}
                          </div>
                          <span className="truncate text-xs">
                            {resolvedAssigneeName || "Unassigned"}
                          </span>
                        </div>
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="unassigned" className="text-xs">
                          Unassigned
                        </SelectItem>
                        {allUsers
                          ?.filter(
                            (u: any) =>
                              selectedTicket.rooms?.some((r: any) => u.room_ids?.includes(r.id)) ||
                              u.id === assigneeId
                          )
                          .map((u: any) => (
                            <SelectItem key={u.id} value={u.id} className="text-xs">
                              {u.staff_id ? `[${u.staff_id}] ` : ""}
                              {u.name}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Due Date – editable by anyone */}
                  <div>
                    <PropLabel>Due Date</PropLabel>
                    <Input
                      type="datetime-local"
                      className="h-8 border-slate-200 text-xs bg-slate-50 hover:bg-slate-100"
                      value={dueDate}
                      onChange={(e) => setDueDate(e.target.value)}
                      onBlur={handleDueDateBlur}
                    />
                    {isOverdue && (
                      <p className="text-[10px] text-red-500 mt-1 font-bold uppercase tracking-wider">
                        Overdue
                      </p>
                    )}
                  </div>

                  <Separator className="bg-slate-100" />

                  {/* Rooms */}
                  <div>
                    <PropLabel>Rooms</PropLabel>
                    <div className="flex flex-wrap gap-1">
                      {selectedTicket.rooms?.length > 0 ? (
                        selectedTicket.rooms.map((room: any) => (
                          <Badge
                            key={room.id}
                            variant="secondary"
                            className="bg-slate-100 text-slate-600 border border-slate-200 text-[10px] px-1.5 py-0.5 font-medium"
                          >
                            {room.name}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-xs text-slate-400">None</span>
                      )}
                    </div>
                  </div>

                  {/* Escalate */}
                  <div>
                    <PropLabel>Escalate To</PropLabel>
                    <Select
                      value="placeholder"
                      onValueChange={(val) => updateTicketMutation.mutate({ add_room_id: val })}
                      disabled={updateTicketMutation.isPending || selectedTicket.status === "resolved"}
                    >
                      <SelectTrigger className="h-8 w-full border-slate-200 text-xs bg-slate-50 hover:bg-slate-100">
                        <SelectValue placeholder="Add department…" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="placeholder" disabled className="text-xs">
                          Select department…
                        </SelectItem>
                        {allRooms
                          ?.filter(
                            (r: any) => !selectedTicket.rooms?.some((tr: any) => tr.id === r.id)
                          )
                          .map((r: any) => (
                            <SelectItem key={r.id} value={r.id} className="text-xs">
                              {r.name}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <Separator className="bg-slate-100" />

                  {/* Created By */}
                  <div>
                    <PropLabel>Created By</PropLabel>
                    <div className="flex items-center gap-2 mt-0.5">
                      <div className="w-7 h-7 rounded-full bg-slate-200 text-slate-700 text-xs font-bold flex items-center justify-center shrink-0">
                        {selectedTicket.creator?.name?.charAt(0)}
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-slate-800 truncate">
                          {selectedTicket.creator?.name}
                        </p>
                        {selectedTicket.creator?.staff_id && (
                          <p className="text-[10px] text-slate-400 font-mono">
                            [{selectedTicket.creator.staff_id}]
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Opened */}
                  <div>
                    <PropLabel>Opened</PropLabel>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      {formatDateTime(selectedTicket.created_at)}
                    </p>
                  </div>
                </div>
              </div>

            </div>
          ) : null}
        </div>
      ) : (
        <div className="hidden md:flex flex-1 flex-col items-center justify-center bg-slate-50/30">
          <Ticket className="w-14 h-14 mb-4 text-slate-200" />
          <p className="text-base font-medium text-slate-500">Select a ticket to view details</p>
          <p className="text-sm text-slate-400 mt-1 max-w-xs text-center">
            Click any ticket to see its full details and activity log.
          </p>
        </div>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 flex justify-center">
          <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
        </div>
      }
    >
      <DashboardContent />
    </Suspense>
  );
}
