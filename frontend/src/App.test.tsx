import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import App from './App';
vi.mock('./Map',()=>({CityMap:()=> <div>Map</div>}));
afterEach(()=>{cleanup();vi.restoreAllMocks();});
it('shows explicit empty state and submits hypothetical scenario',async()=>{
 const mock=vi.spyOn(globalThis,'fetch').mockImplementation(async(input,init)=>{
  const path=String(input);const data=path.endsWith('agents/health')?{}:path.endsWith('assessments')?{unavailable_dimensions:['heat']}:[];
  return new Response(JSON.stringify(data),{status:200});
 });
 render(<App/>);
 expect(await screen.findByText(/No observations available/)).toBeInTheDocument();
 fireEvent.click(screen.getByText('Assess heat scenario'));
 await waitFor(()=>expect(mock).toHaveBeenCalledWith('/api/v1/assessments',expect.objectContaining({method:'POST',body:expect.stringContaining('temperature_delta_c')})));
 expect(await screen.findByLabelText('Analysis result')).toHaveTextContent('unavailable_dimensions');
});
it('shows API failure instead of pretending to have loaded data',async()=>{
 vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response('error',{status:503}));render(<App/>);
 expect(await screen.findByRole('alert')).toHaveTextContent('503');
});
