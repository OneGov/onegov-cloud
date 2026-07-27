import {useEffect, useState} from 'react';


export function useJsonResource(endpoint) {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        const controller = new AbortController();
        setData(null);
        setError(null);

        fetch(endpoint, {
            headers: {Accept: 'application/json'},
            signal: controller.signal
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return response.json();
            })
            .then(setData)
            .catch((requestError) => {
                if (requestError.name !== 'AbortError') {
                    setError(requestError);
                }
            });

        return () => controller.abort();
    }, [endpoint]);

    return {data, error, loading: !data && !error};
}
