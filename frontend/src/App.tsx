import { Route, Routes } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard/Dashboard";
import { BoardPage } from "./pages/Board/BoardPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/boards/:boardId" element={<BoardPage />} />
      <Route
        path="*"
        element={
          <div className="mx-auto max-w-md px-4 py-16 text-center">
            <p className="text-sm text-slate-500">Page not found.</p>
          </div>
        }
      />
    </Routes>
  );
}
