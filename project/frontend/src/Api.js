export default function fetchSettings() {
  return fetch('/api/settings').then((response) => response.json());
}

export function fetchScenes() {
  return fetch('/api/geolayer/scene').then((response) => response.json());
}
