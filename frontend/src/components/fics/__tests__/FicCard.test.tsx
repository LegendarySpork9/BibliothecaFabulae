import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import type { FicSummary } from "../../../types/fic";
import { FicCard } from "../FicCard";

function makeFic(overrides?: Partial<FicSummary>): FicSummary {
  return {
    id: 1,
    source_site: "ao3",
    source_id: "12345",
    title: "The Great Adventure",
    rating: "Teen And Up Audiences",
    word_count: 85_432,
    chapter_count: 12,
    is_complete: true,
    is_favourite: false,
    is_source_available: true,
    import_method: "manual",
    date_archived: "2024-06-15T10:30:00Z",
    authors: [{ id: 1, name: "TestAuthor" }],
    ...overrides,
  };
}

function renderFicCard(fic: FicSummary) {
  return render(
    <MemoryRouter>
      <FicCard fic={fic} />
    </MemoryRouter>
  );
}

describe("FicCard", () => {
  it("renders the fic title", () => {
    renderFicCard(makeFic());

    expect(screen.getByText("The Great Adventure")).toBeInTheDocument();
  });

  it("renders the author name", () => {
    renderFicCard(makeFic());

    expect(screen.getByText("TestAuthor")).toBeInTheDocument();
  });

  it("renders multiple authors joined by comma", () => {
    renderFicCard(
      makeFic({
        authors: [
          { id: 1, name: "Alice" },
          { id: 2, name: "Bob" },
        ],
      })
    );

    expect(screen.getByText("Alice, Bob")).toBeInTheDocument();
  });

  it("displays Unknown Author when authors is empty", () => {
    renderFicCard(makeFic({ authors: [] }));

    expect(screen.getByText("Unknown Author")).toBeInTheDocument();
  });

  it("renders the site label as AO3", () => {
    renderFicCard(makeFic({ source_site: "ao3" }));

    expect(screen.getByText("AO3")).toBeInTheDocument();
  });

  it("renders the rating badge", () => {
    renderFicCard(makeFic({ rating: "Mature" }));

    expect(screen.getByText("Mature")).toBeInTheDocument();
  });

  it("does not render a rating badge when rating is null", () => {
    renderFicCard(makeFic({ rating: null }));

    expect(screen.queryByText("Mature")).not.toBeInTheDocument();
  });

  it("renders chapter count", () => {
    renderFicCard(makeFic({ chapter_count: 12 }));

    expect(screen.getByText("12 ch")).toBeInTheDocument();
  });

  it("formats word count in K for thousands", () => {
    renderFicCard(makeFic({ word_count: 85_432 }));

    expect(screen.getByText("85K words")).toBeInTheDocument();
  });

  it("formats word count in M for millions", () => {
    renderFicCard(makeFic({ word_count: 1_500_000 }));

    expect(screen.getByText("1.5M words")).toBeInTheDocument();
  });

  it("displays em dash for null word count", () => {
    renderFicCard(makeFic({ word_count: null }));

    expect(screen.getByText(/— words/)).toBeInTheDocument();
  });

  it("renders a small word count as plain number", () => {
    renderFicCard(makeFic({ word_count: 500 }));

    expect(screen.getByText("500 words")).toBeInTheDocument();
  });

  it("links to the fic detail page", () => {
    renderFicCard(makeFic({ id: 42 }));

    const link = screen.getByRole("link");

    expect(link).toHaveAttribute("href", "/library/42");
  });

  it("renders the raw site key when no label mapping exists", () => {
    renderFicCard(makeFic({ source_site: "unknownsite" }));

    expect(screen.getByText("unknownsite")).toBeInTheDocument();
  });
});
