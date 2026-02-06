export default function AppProviders({ children }) {
  return (
    <>
      <s-app-nav>
        <s-link href="/app" rel="home">
          Home
        </s-link>
        <s-link href="/app/products">Products</s-link>
        <s-link href="/app/inventory">Inventory</s-link>
        <s-link href="/app/orders">Orders</s-link>
        <s-link href="/app/jobs">Jobs</s-link>
        <s-link href="/app/settings">Settings</s-link>
      </s-app-nav>
      {children}
    </>
  );
}