/**
 * Projects landing — placeholder scaffold. Filled in Task 1.1.
 */
export default function Projects() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <h1 className="text-lg font-semibold">Projects</h1>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="rounded-lg border-2 border-dashed border-slate-300 p-16 text-center">
          <p className="text-slate-500">
            No projects yet. You&rsquo;ll see invitations here when UserCue sends
            them.
          </p>
        </div>
      </main>
    </div>
  );
}
