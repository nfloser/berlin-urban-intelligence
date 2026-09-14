import {useEffect,useRef,useState} from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
export function CityMap(){
 const container=useRef<HTMLDivElement>(null);
 const [error,setError]=useState('');
 useEffect(()=>{
  if(!container.current)return;
  let map:maplibregl.Map;
  try{
   map=new maplibregl.Map({container:container.current,center:[13.405,52.52],zoom:10,style:{version:8,sources:{osm:{type:'raster',tiles:['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],tileSize:256,attribution:'© OpenStreetMap contributors'}},layers:[{id:'base',type:'raster',source:'osm'}]}});
   map.addControl(new maplibregl.NavigationControl());
   map.on('load',()=>{
    map.addSource('urban',{type:'geojson',data:'/api/v1/map'});
    map.addLayer({id:'climate',type:'fill',source:'urban',filter:['==',['geometry-type'],'Polygon'],paint:{'fill-color':'#d99450','fill-opacity':0.3}});
    map.addLayer({id:'locations',type:'circle',source:'urban',filter:['==',['geometry-type'],'Point'],paint:{'circle-radius':5,'circle-color':'#72e5c0','circle-stroke-color':'#123a32','circle-stroke-width':1}});
    map.on('click','locations',event=>{const f=event.features?.[0];if(f)new maplibregl.Popup().setLngLat(event.lngLat).setText(String(f.properties?.label||f.properties?.id)).addTo(map);});
   });
   map.on('error',()=>setError('Some map layers could not load. Measurements remain available below.'));
  }catch{setError('Map unavailable: this device does not provide WebGL.');}
  return ()=>map?.remove();
 },[]);
 return <section className="map-panel"><div ref={container} className="map" aria-label="Berlin reference map"/><div className="map-caption">BERLIN · EPSG:4326 <span>Only geolocated source records are plotted</span></div>{error&&<p role="status">{error}</p>}</section>;
}
