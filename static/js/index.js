import '../css./styles.css'; 
import { createRoot } from 'react-dom/client';
import { Navigation } from './components.js';

function NavigationBar() {
  // TODO: Actually implement a navigation bar
  return <h1>Hello from React!</h1>;
}

const domNode = document.getElementById('navigation');
const root = createRoot(domNode);
root.render(<NavigationBar />);