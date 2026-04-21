import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import Inventory from "@/pages/Inventory";
import { SCHEMA_AREAS } from "@/inventory/data";

function renderInventory() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <Inventory />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Inventory page", () => {
  it("renders all top-level section headings", () => {
    renderInventory();
    expect(screen.getByRole("heading", { name: /M0 inventory/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /live components/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /canonical schema/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /event types/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /security guardrails/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /test coverage/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /git log/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /M0 tasks complete/i })).toBeInTheDocument();
  });

  it("lists all canonical tables", () => {
    renderInventory();
    const allTableNames = SCHEMA_AREAS.flatMap((a) => a.tables.map((t) => t.name));
    expect(allTableNames.length).toBeGreaterThanOrEqual(22);
    for (const name of allTableNames) {
      const matches = screen.getAllByText(name);
      expect(matches.length).toBeGreaterThanOrEqual(1);
    }
  });

  it("impersonation toggle exposes a button that flips state", () => {
    renderInventory();
    const toggle = screen.getByRole("button", { name: /impersonation off/i });
    expect(toggle).toBeInTheDocument();
    fireEvent.click(toggle);
    expect(
      screen.getByRole("button", { name: /impersonation active/i }),
    ).toBeInTheDocument();
  });
});
