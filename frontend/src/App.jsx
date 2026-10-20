import { useEffect, useState } from "react";
import "./App.css";
import React from "react";


const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
;

export default function App() {
  const [products, setProducts] = useState([]);
  const [summary, setSummary] = useState({
    total_products: 0,
    total_units: 0,
    low_stock_count: 0,
  });
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [modal, setModal] = useState("");
  const [selected, setSelected] = useState(null);
  const [history, setHistory] = useState([]);
  const [form, setForm] = useState({
    name: "",
    price: "",
    quantity: "",
  });
  const [movementQuantity, setMovementQuantity] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");

  async function request(path, options = {}) {
    const response = await fetch(`${API}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    const data =
      response.status === 204 ? null : await response.json().catch(() => null);

    if (!response.ok) {
      throw new Error(data?.detail || "Something went wrong");
    }

    return data;
  }

  async function loadData() {
    setLoading(true);
    setError("");

    try {
      const [productData, summaryData] = await Promise.all([
        request("/products"),
        request("/summary"),
      ]);

      setProducts(productData);
      setSummary(summaryData);
    } catch (err) {
      setError(err.message || "Unable to connect to StockWise API.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const filtered = products.filter((product) =>
    product.name.toLowerCase().includes(search.toLowerCase()),
  );

  function openCreate() {
    setSelected(null);
    setForm({ name: "", price: "", quantity: "" });
    setModal("product");
  }

  function openEdit(product) {
    setSelected(product);
    setForm({
      name: product.name,
      price: product.price,
      quantity: product.quantity,
    });
    setModal("product");
  }

  async function saveProduct(event) {
    event.preventDefault();
    setBusy(true);
    setNotice("");

    try {
      const payload = {
        name: form.name.trim(),
        price: Number(form.price),
        quantity: Number(form.quantity),
      };

      if (selected) {
        await request(`/products/${selected.id}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        setNotice("Product updated successfully.");
      } else {
        await request("/products", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        setNotice("Product added successfully.");
      }

      setModal("");
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function deleteProduct(product) {
    if (!window.confirm(`Delete "${product.name}"?`)) return;

    setError("");
    setNotice("");

    try {
      await request(`/products/${product.id}`, { method: "DELETE" });
      setNotice("Product deleted successfully.");
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  }

  async function openMovement(product, type) {
    setSelected(product);
    setMovementQuantity("");
    setModal(type);
  }

  async function saveMovement(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");

    try {
      const type = modal;
      await request(`/products/${selected.id}/stock-${type}`, {
        method: "POST",
        body: JSON.stringify({ quantity: Number(movementQuantity) }),
      });

      setModal("");
      setNotice(
        type === "in"
          ? "Stock received successfully."
          : "Stock issued successfully.",
      );
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function openHistory(product) {
    setSelected(product);
    setError("");

    try {
      const data = await request(`/products/${product.id}/history`);
      setHistory(data);
      setModal("history");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">S</div>
          <div>
            <strong>StockWise</strong>
            <span>INVENTORY CONTROL</span>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <div className="nav-item active">
          <span>▦</span> Dashboard
        </div>
        <div
          className="nav-item"
          onClick={() =>
            document
              .getElementById("inventory")
              ?.scrollIntoView({ behavior: "smooth" })
          }
        >
          <span>▤</span> Products
        </div>
        <div className="sidebar-bottom">
          <div className="status-dot" />
          <div>
            <strong>StockWise API</strong>
            <span>Local development</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span> Dashboard
          </div>
          <div className="profile">
            <div className="profile-avatar">SW</div>
            <div>
              <strong>Inventory Admin</strong>
              <span>Administrator</span>
            </div>
          </div>
        </header>

        <section className="page-heading">
          <div>
            <div className="eyebrow">OVERVIEW</div>
            <h1>Inventory dashboard</h1>
            <p>Track products, monitor stock levels, and manage inventory.</p>
          </div>
          <button className="primary-button" onClick={openCreate}>
            <span>＋</span> Add product
          </button>
        </section>

        {error && (
          <div className="alert error-alert">
            <span>{error}</span>
            <button onClick={() => setError("")}>×</button>
          </div>
        )}
        {notice && (
          <div className="alert success-alert">
            <span>{notice}</span>
            <button onClick={() => setNotice("")}>×</button>
          </div>
        )}

        <section className="stats-grid">
          <div className="stat-card">
            <div className="stat-top">
              <span>Total products</span>
              <div className="stat-icon purple">▤</div>
            </div>
            <h2>{loading ? "—" : summary.total_products}</h2>
            <p>Products in your inventory</p>
          </div>
          <div className="stat-card">
            <div className="stat-top">
              <span>Total units</span>
              <div className="stat-icon blue">▦</div>
            </div>
            <h2>{loading ? "—" : summary.total_units}</h2>
            <p>Units currently in stock</p>
          </div>
          <div className="stat-card">
            <div className="stat-top">
              <span>Low-stock products</span>
              <div className="stat-icon orange">⚠</div>
            </div>
            <h2>{loading ? "—" : summary.low_stock_count}</h2>
            <p>Products with fewer than 5 units</p>
          </div>
        </section>

        <section className="inventory-section" id="inventory">
          <div className="section-heading">
            <div>
              <h2>Product inventory</h2>
              <p>Manage products and stock movements.</p>
            </div>
            <button className="secondary-button" onClick={loadData}>
              ↻ Refresh
            </button>
          </div>

          <div className="table-toolbar">
            <div className="search-box">
              <span>⌕</span>
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search products..."
              />
            </div>
            <span className="result-count">{filtered.length} products</span>
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>PRODUCT</th>
                  <th>PRICE</th>
                  <th>QUANTITY</th>
                  <th>STOCK STATUS</th>
                  <th>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="5" className="empty-state">
                      Loading inventory...
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="empty-state">
                      No products found. Add your first product.
                    </td>
                  </tr>
                ) : (
                  filtered.map((product) => (
                    <tr key={product.id}>
                      <td>
                        <div className="product-cell">
                          <div className="product-avatar">
                            {product.name.slice(0, 1).toUpperCase()}
                          </div>
                          <div>
                            <strong>{product.name}</strong>
                            <span>
                              SKU-{String(product.id).padStart(4, "0")}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td className="price-cell">
                        ₹
                        {Number(product.price).toLocaleString("en-IN", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </td>
                      <td>
                        <strong>{product.quantity}</strong>{" "}
                        <span className="unit-label">units</span>
                      </td>
                      <td>
                        <span
                          className={`status-pill ${product.quantity < 5 ? "low" : product.quantity < 10 ? "medium" : "healthy"}`}
                        >
                          <span />{" "}
                          {product.quantity < 5
                            ? "Low stock"
                            : product.quantity < 10
                              ? "Running low"
                              : "In stock"}
                        </span>
                      </td>
                      <td>
                        <div className="actions">
                          <button
                            title="Stock in"
                            onClick={() => openMovement(product, "in")}
                          >
                            ＋
                          </button>
                          <button
                            title="Stock out"
                            onClick={() => openMovement(product, "out")}
                          >
                            −
                          </button>
                          <button
                            title="History"
                            onClick={() => openHistory(product)}
                          >
                            ◷
                          </button>
                          <button
                            title="Edit"
                            onClick={() => openEdit(product)}
                          >
                            ✎
                          </button>
                          <button
                            title="Delete"
                            className="delete-action"
                            onClick={() => deleteProduct(product)}
                          >
                            ⌫
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <div className="table-footer">
            Showing {filtered.length} of {products.length} products
          </div>
        </section>

        <footer className="footer">
          <span>StockWise Inventory Management</span>
          <span>Built with React · FastAPI · PostgreSQL</span>
        </footer>
      </main>

      {modal && (
        <div
          className="modal-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setModal("");
          }}
        >
          <div className="modal">
            <div className="modal-heading">
              <div>
                <h2>
                  {modal === "product"
                    ? selected
                      ? "Edit product"
                      : "Add product"
                    : modal === "in"
                      ? "Receive stock"
                      : modal === "out"
                        ? "Issue stock"
                        : "Stock movement history"}
                </h2>
                <p>
                  {modal === "history"
                    ? selected?.name
                    : modal === "product"
                      ? "Enter product details below."
                      : `Product: ${selected?.name}`}
                </p>
              </div>
              <button className="close-button" onClick={() => setModal("")}>
                ×
              </button>
            </div>

            {modal === "product" && (
              <form onSubmit={saveProduct}>
                <label>
                  Product name
                  <input
                    required
                    minLength="1"
                    maxLength="100"
                    value={form.name}
                    onChange={(event) =>
                      setForm({ ...form, name: event.target.value })
                    }
                    placeholder="e.g. Wireless Keyboard"
                  />
                </label>
                <label>
                  Price (₹)
                  <input
                    required
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={form.price}
                    onChange={(event) =>
                      setForm({ ...form, price: event.target.value })
                    }
                    placeholder="0.00"
                  />
                </label>
                <label>
                  Quantity
                  <input
                    required
                    type="number"
                    min="0"
                    step="1"
                    value={form.quantity}
                    onChange={(event) =>
                      setForm({ ...form, quantity: event.target.value })
                    }
                    placeholder="0"
                  />
                </label>
                <div className="modal-actions">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => setModal("")}
                  >
                    Cancel
                  </button>
                  <button disabled={busy} className="primary-button">
                    {busy ? "Saving..." : "Save product"}
                  </button>
                </div>
              </form>
            )}

            {(modal === "in" || modal === "out") && (
              <form onSubmit={saveMovement}>
                <div className="movement-info">
                  Current stock <strong>{selected?.quantity} units</strong>
                </div>
                <label>
                  Quantity
                  <input
                    required
                    type="number"
                    min="1"
                    step="1"
                    value={movementQuantity}
                    onChange={(event) =>
                      setMovementQuantity(event.target.value)
                    }
                    placeholder="Enter quantity"
                  />
                </label>
                <div className="modal-actions">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => setModal("")}
                  >
                    Cancel
                  </button>
                  <button disabled={busy} className="primary-button">
                    {busy
                      ? "Processing..."
                      : modal === "in"
                        ? "Receive stock"
                        : "Issue stock"}
                  </button>
                </div>
              </form>
            )}

            {modal === "history" && (
              <div>
                {history.length === 0 ? (
                  <div className="empty-state">
                    No stock movements recorded yet.
                  </div>
                ) : (
                  <div className="history-list">
                    {history.map((item, index) => (
                      <div
                        className="history-item"
                        key={
                          item.id ??
                          `${item.movement_type}-${item.created_at}-${index}`
                        }
                      >
                        <div
                          className={`history-icon ${item.movement_type === "IN" ? "history-in" : "history-out"}`}
                        >
                          {item.movement_type === "IN" ? "＋" : "−"}
                        </div>
                        <div className="history-description">
                          <strong>
                            Stock{" "}
                            {item.movement_type === "IN"
                              ? "received"
                              : "issued"}
                          </strong>
                          <span>
                            {item.created_at
                              ? new Date(item.created_at).toLocaleString()
                              : "Date unavailable"}
                          </span>
                        </div>
                        <strong>
                          {item.movement_type === "IN" ? "+" : "−"}
                          {item.quantity}
                        </strong>
                      </div>
                    ))}
                  </div>
                )}
                <div className="modal-actions">
                  <button
                    className="primary-button"
                    onClick={() => setModal("")}
                  >
                    Done
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
