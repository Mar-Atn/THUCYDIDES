/**
 * App — root component with routing.
 */

import { Routes, Route, Navigate } from 'react-router-dom'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { Login } from '@/pages/Login'
import { Register } from '@/pages/Register'
import { ResetPassword } from '@/pages/ResetPassword'
import { UpdatePassword } from '@/pages/UpdatePassword'
import { Dashboard } from '@/pages/Dashboard'
import { PendingApproval } from '@/pages/PendingApproval'
import { AISetup } from '@/pages/AISetup'
import { UserManagement } from '@/pages/UserManagement'
import { SimRunWizard } from '@/pages/SimRunWizard'
import { TemplateList } from '@/pages/TemplateList'
import { TemplateEditor } from '@/pages/TemplateEditor'
import { FacilitatorDashboard } from '@/pages/FacilitatorDashboard'

export function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/update-password" element={<UpdatePassword />} />

      {/* Protected routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/pending"
        element={
          <ProtectedRoute>
            <PendingApproval />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/ai-setup"
        element={
          <ProtectedRoute>
            <AISetup />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/users"
        element={
          <ProtectedRoute>
            <UserManagement />
          </ProtectedRoute>
        }
      />

      {/* Template management */}
      <Route
        path="/admin/templates"
        element={
          <ProtectedRoute>
            <TemplateList />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/templates/:id/edit"
        element={
          <ProtectedRoute>
            <TemplateEditor />
          </ProtectedRoute>
        }
      />

      {/* SimRun wizard — create and edit */}
      <Route
        path="/sim/create"
        element={
          <ProtectedRoute>
            <SimRunWizard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/sim/:id/edit"
        element={
          <ProtectedRoute>
            <SimRunWizard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/sim/:id/live"
        element={
          <ProtectedRoute>
            <FacilitatorDashboard />
          </ProtectedRoute>
        }
      />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
