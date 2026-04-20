"""L1 — Hex adjacency tests for pointy-top odd-r offset convention."""

import pytest
from engine.config.map_config import hex_neighbors, hex_neighbors_bounded, GLOBAL_ROWS, GLOBAL_COLS


class TestHexNeighbors:
    """Verify adjacency formula matches the canonical odd-r offset convention."""

    def test_odd_row_center(self):
        """Odd row (3), center of map — should have 6 neighbors."""
        n = hex_neighbors(3, 5)
        assert len(n) == 6
        # 1-indexed odd row (not shifted): (-1,-1) (-1,0) (0,-1) (0,+1) (+1,-1) (+1,0)
        assert set(n) == {(2, 4), (2, 5), (3, 4), (3, 6), (4, 4), (4, 5)}

    def test_even_row_center(self):
        """Even row (4), center of map — should have 6 neighbors."""
        n = hex_neighbors(4, 5)
        assert len(n) == 6
        # 1-indexed even row (shifted right): (-1,0) (-1,+1) (0,-1) (0,+1) (+1,0) (+1,+1)
        assert set(n) == {(3, 5), (3, 6), (4, 4), (4, 6), (5, 5), (5, 6)}

    def test_row_1_col_1_corner(self):
        """Top-left corner — 6 raw neighbors, some out of bounds."""
        n = hex_neighbors(1, 1)
        assert len(n) == 6
        # Row 1 is odd (not shifted): (-1,-1)=(0,0) (-1,0)=(0,1) (0,-1)=(1,0) (0,+1)=(1,2) (+1,-1)=(2,0) (+1,0)=(2,1)
        assert (0, 0) in n  # out of bounds
        assert (1, 0) in n  # out of bounds
        assert (2, 1) in n  # valid

    def test_bounded_filters_edges(self):
        """Bounded version filters out-of-bounds neighbors."""
        n = hex_neighbors_bounded(1, 1, max_rows=GLOBAL_ROWS, max_cols=GLOBAL_COLS)
        for r, c in n:
            assert 1 <= r <= GLOBAL_ROWS
            assert 1 <= c <= GLOBAL_COLS

    def test_bounded_corner_count(self):
        """Corner hex has fewer bounded neighbors than center hex."""
        corner = hex_neighbors_bounded(1, 1)
        center = hex_neighbors_bounded(5, 10)
        assert len(corner) < len(center)
        assert len(center) == 6

    def test_symmetry(self):
        """If A is neighbor of B, then B is neighbor of A."""
        for row in range(1, 6):
            for col in range(1, 6):
                for nr, nc in hex_neighbors(row, col):
                    neighbors_of_neighbor = hex_neighbors(nr, nc)
                    assert (row, col) in neighbors_of_neighbor, \
                        f"({row},{col}) is neighbor of ({nr},{nc}) but not vice versa"

    def test_theater_grid(self):
        """Theater grid (10x10) bounded adjacency works."""
        n = hex_neighbors_bounded(5, 5, max_rows=10, max_cols=10)
        assert len(n) == 6  # center of 10x10, all neighbors in bounds
