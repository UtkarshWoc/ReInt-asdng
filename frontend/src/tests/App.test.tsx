import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "../App";

describe("App Scaffold", () => {
  it("renders header title and tabs", () => {
    render(<App />);
    expect(screen.getByText("UK Wind Day-Ahead Decision Support")).toBeInTheDocument();
    expect(screen.getByText("Forecast at Decision")).toBeInTheDocument();
    expect(screen.getByText("Forecast Accuracy")).toBeInTheDocument();
  });
});
